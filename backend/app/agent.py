"""The RecallDesk agent loop: recall → reason → tools → answer → retain.

Memory is the backbone:

1. **Recall** — before the LLM sees anything, we search the customer's entire
   history in Hindsight (facts + observations + mental models) and inject the
   results into the system prompt.
2. **Reason** — Groq decides, grounded in that memory, whether to call a tool.
3. **Tools** — ground-truth data (orders/tickets/refunds/escalation).
4. **Answer** — final reply, grounded in memory + tool data.
5. **Retain** — every turn is written back to Hindsight with customer + role
   metadata, feeding the next consolidation cycle.

Every response carries `memory_used` so the UI can show *why* the agent
answered the way it did.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional

from . import memory_tools
from .config import settings
from .hindsight_layer import TOOLS_SPEC, hindsight_layer
from .llm import GroqClient, LLMError
from .mental_models import LEARNED_PLAYS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """You are RecallDesk, Acme Cloud's support agent.

CUSTOMER: {customer_name} <{email}>
{memory_block}

LEARNED SUPPORT PLAYS (team mental models):
{plays_block}

Rules:
- Ground every claim in MEMORY CONTEXT or tool results. No invented facts.
- Never ask for anything memory already knows (order number, plan, prior tickets).
- If a learned play applies, apply it before answering.
- If system data contradicts the customer's claim, say so plainly and kindly.
- Keep replies short, warm and specific.
"""

NO_MEMORY_BLOCK = "MEMORY CONTEXT: (none — this customer's history is not available)"

FALLBACK_REPLY = (
    "I'm having trouble reaching my systems right now. I've noted your request and a "
    "specialist will follow up by email — you won't need to repeat anything."
)


@dataclass
class AgentResponse:
    reply: str = ""
    memory_used: List[Dict[str, Any]] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    latency_ms: int = 0
    session_id: str = ""
    used_memory: bool = False


class SupportAgent:
    def __init__(self, llm: Optional[GroqClient] = None) -> None:
        self.llm = llm or GroqClient()

    # ------------------------------------------------------------------
    def _memory_block(self, memories: List[Dict[str, Any]]) -> str:
        if not memories:
            return NO_MEMORY_BLOCK
        lines = ["MEMORY CONTEXT (customer history, most relevant first):"]
        for i, m in enumerate(memories, 1):
            stamp = f" · {str(m.get('created_at', ''))[:10]}" if m.get("created_at") else ""
            lines.append(f"{i}. [{m.get('type', 'fact')}]{stamp} {m['text']}")
        return "\n".join(lines)

    def _plays_block(self, plays: List[Dict[str, Any]]) -> str:
        if not plays:
            return "(none yet — the team hasn't learned any plays)"
        return "\n".join(f"- {p['name']}: {p['text'][:220]}" for p in plays)

    def _build_system_prompt(self, customer_name: str, email: str, memories: List[Dict[str, Any]], use_memory: bool) -> str:
        memory_block = self._memory_block(memories) if use_memory else NO_MEMORY_BLOCK
        plays = LEARNED_PLAYS if use_memory else []
        return SYSTEM_PROMPT_TEMPLATE.format(
            customer_name=customer_name,
            email=email,
            memory_block=memory_block,
            plays_block=self._plays_block(plays),
        )

    # ------------------------------------------------------------------
    def _execute_tool(self, call: Any) -> Dict[str, Any]:
        impl = memory_tools.TOOL_IMPLS.get(call.name)
        if impl is None:
            return {"name": call.name, "arguments": call.arguments, "result": {"error": f"Unknown tool: {call.name}"}}
        try:
            value = json.loads(impl(**call.arguments))
            return {"name": call.name, "arguments": call.arguments, "result": value}
        except TypeError as exc:
            return {"name": call.name, "arguments": call.arguments, "result": {"error": f"Bad arguments for {call.name}: {exc}"}}

    def _run_tools(self, tool_calls: List[Any], history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        executed: List[Dict[str, Any]] = []
        for call in tool_calls:
            outcome = self._execute_tool(call)
            executed.append(outcome)
            payload = outcome["result"] if "result" in outcome else outcome.get("error", {"error": "tool failed"})
            history.append({
                "role": "tool",
                "tool_call_id": call.id or "call_0",
                "content": json.dumps(payload),
            })
        return executed

    def _append_tool_call_message(self, call: Any, history: List[Dict[str, Any]]) -> None:
        history.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": call.id or "call_0",
                "type": "function",
                "function": {"name": call.name, "arguments": json.dumps(call.arguments)},
            }],
        })

    # ------------------------------------------------------------------
    def _tool_loop(self, history: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
        """Run the bounded reason→tool loop. Returns (reply, executed_tools)."""
        executed: List[Dict[str, Any]] = []
        for _ in range(settings.max_tool_iterations):
            try:
                llm_resp = self.llm.chat(messages=history, tools=TOOLS_SPEC)
            except LLMError:
                logger.exception("LLM failure during tool loop")
                return FALLBACK_REPLY, executed

            if not llm_resp.tool_calls:
                return (llm_resp.content.strip() or "Let me look into that for you."), executed

            for call in llm_resp.tool_calls:
                self._append_tool_call_message(call, history)
            executed.extend(self._run_tools(llm_resp.tool_calls, history))

        return (
            "I want to make sure I get this exactly right, so I'm bringing in a specialist "
            "who will follow up by email.",
            executed,
        )

    # ------------------------------------------------------------------
    def respond(self, *, customer_email: str, customer_name: str, message: str,
                session_id: Optional[str] = None, use_memory: bool = True) -> AgentResponse:
        started = time.time()
        session_id = session_id or f"chat-{uuid.uuid4().hex[:8]}"
        doc_id = f"chat-{session_id}"

        # 1) RECALL — memory before the model.
        memories: List[Dict[str, Any]] = []
        if use_memory:
            memories = hindsight_layer.recall(
                query=f"Customer {customer_name} ({customer_email}): {message}",
                types=["world", "experience", "observation"],
            )

        history: List[Dict[str, Any]] = [
            {"role": "system", "content": self._build_system_prompt(customer_name, customer_email, memories, use_memory)},
            {"role": "user", "content": message},
        ]

        # 2+3) REASON + TOOLS.
        reply, executed = self._tool_loop(history)

        # 4) RETAIN — write the turn back to memory.
        if use_memory:
            hindsight_layer.retain_interaction(
                customer_email=customer_email, role="customer", text=message,
                document_id=doc_id, metadata={"session_id": session_id},
            )
            hindsight_layer.retain_interaction(
                customer_email=customer_email, role="agent", text=reply,
                document_id=doc_id, metadata={"session_id": session_id},
            )

        return AgentResponse(
            reply=reply,
            memory_used=memories,
            tool_calls=executed,
            latency_ms=int((time.time() - started) * 1000),
            session_id=session_id,
            used_memory=use_memory,
        )

    # ------------------------------------------------------------------
    def stream_respond(self, *, customer_email: str, customer_name: str, message: str,
                       session_id: Optional[str] = None, use_memory: bool = True) -> Generator[Dict[str, Any], None, None]:
        """SSE-friendly variant: yields {'type': ...} events, ending with 'done'."""
        started = time.time()
        session_id = session_id or f"chat-{uuid.uuid4().hex[:8]}"
        doc_id = f"chat-{session_id}"

        memories: List[Dict[str, Any]] = []
        if use_memory:
            memories = hindsight_layer.recall(
                query=f"Customer {customer_name} ({customer_email}): {message}",
                types=["world", "experience", "observation"],
            )
        yield {"type": "memories", "memories": memories, "used_memory": use_memory}

        history: List[Dict[str, Any]] = [
            {"role": "system", "content": self._build_system_prompt(customer_name, customer_email, memories, use_memory)},
            {"role": "user", "content": message},
        ]

        executed: List[Dict[str, Any]] = []
        reply = ""
        for _ in range(settings.max_tool_iterations):
            try:
                llm_resp = self.llm.chat(messages=history, tools=TOOLS_SPEC)
            except LLMError:
                logger.exception("LLM failure during streaming tool loop")
                reply = FALLBACK_REPLY
                break

            if not llm_resp.tool_calls:
                # Final answer: stream it token by token.
                streamed = ""
                try:
                    for piece in self.llm.stream_chat(messages=history):
                        streamed += piece
                        yield {"type": "delta", "text": piece}
                except LLMError:
                    logger.exception("Streaming failed; falling back to full reply")
                reply = streamed.strip() or llm_resp.content.strip() or FALLBACK_REPLY
                if not streamed.strip():
                    yield {"type": "delta", "text": reply}
                break

            for call in llm_resp.tool_calls:
                self._append_tool_call_message(call, history)
            executed.extend(self._run_tools(llm_resp.tool_calls, history))
        else:
            reply = ("I want to make sure I get this exactly right, so I'm bringing in a specialist "
                     "who will follow up by email.")
            yield {"type": "delta", "text": reply}

        if use_memory:
            hindsight_layer.retain_interaction(
                customer_email=customer_email, role="customer", text=message,
                document_id=doc_id, metadata={"session_id": session_id},
            )
            hindsight_layer.retain_interaction(
                customer_email=customer_email, role="agent", text=reply,
                document_id=doc_id, metadata={"session_id": session_id},
            )

        yield {
            "type": "done",
            "reply": reply,
            "tool_calls": executed,
            "latency_ms": int((time.time() - started) * 1000),
            "session_id": session_id,
        }


support_agent = SupportAgent()
