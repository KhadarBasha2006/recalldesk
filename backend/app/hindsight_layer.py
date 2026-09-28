"""Thin wrapper around the Hindsight client.

Everything the agent knows lives here.  All operations go through this layer so
the rest of the codebase never imports `hindsight_client` directly — which makes
the whole app easy to mock in tests and to point at Hindsight Cloud later.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from .config import settings

logger = logging.getLogger(__name__)

MISSION = (
    "You are RecallDesk, the support agent for Acme Cloud. You know each customer's "
    "full history: devices, plans, past tickets, refunds and outcomes. You resolve "
    "issues on first contact when possible and never ask a customer to repeat "
    "information the company already has."
)

DIRECTIVES = [
    "Never ask the customer for their order number if memory already has it.",
    "Always check memory for prior unresolved complaints before proposing a fix.",
    "Never promise a refund amount; state policy and offer the exact next step.",
    "If system data and the customer's claim conflict, say so plainly and kindly.",
]

DISPOSITION = {"skepticism": 2, "literalism": 2, "empathy": 5}

_SYSTEM_PROMPT = (
    "You are RecallDesk, Acme Cloud's support agent.\n"
    "Answer the customer's message using the MEMORY CONTEXT and, when relevant, tool results.\n"
    "Rules:\n"
    "- Use recalled memories as your primary knowledge of this customer.\n"
    "- Never ask for information already present in memory (order number, plan, prior tickets).\n"
    "- If memory contains a relevant learned play, follow it.\n"
    "- Be warm, specific and brief. Reference the customer's actual history, not generic sympathy.\n"
    "- If MEMORY CONTEXT is empty, say you could not find prior history and help from scratch.\n"
)

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": "Look up a customer order by id (ground-truth system of record).",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "e.g. ORD-7741"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_orders",
            "description": "List orders for a customer email (ground-truth system of record).",
            "parameters": {
                "type": "object",
                "properties": {"email": {"type": "string", "description": "customer email"}},
                "required": ["email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ticket",
            "description": "Look up a support ticket by id (ground-truth system of record).",
            "parameters": {
                "type": "object",
                "properties": {"ticket_id": {"type": "string", "description": "e.g. TCK-1043"}},
                "required": ["ticket_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tickets",
            "description": "List support tickets for a customer email (ground-truth system of record).",
            "parameters": {
                "type": "object",
                "properties": {"email": {"type": "string"}},
                "required": ["email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "approve_refund",
            "description": "Record a refund decision for an order (≤ $200 auto-approved).",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "amount": {"type": "number"},
                    "reason": {"type": "string"},
                },
                "required": ["order_id", "amount", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate",
            "description": "Escalate a case to a human specialist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "reason": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["ticket_id", "reason", "summary"],
            },
        },
    },
]


class HindsightLayer:
    """All Hindsight operations used by RecallDesk, in one place."""

    def __init__(self) -> None:
        self._client: Any = None

    # -- lifecycle ---------------------------------------------------------
    def _ensure_client(self) -> Any:
        if self._client is None:
            from hindsight_client import Hindsight  # imported lazily for testability

            kwargs: Dict[str, Any] = {"base_url": settings.hindsight_base_url}
            if settings.hindsight_api_key:
                kwargs["api_key"] = settings.hindsight_api_key
            self._client = Hindsight(**kwargs)
        return self._client

    # -- bank --------------------------------------------------------------
    def ensure_bank(self) -> None:
        client = self._ensure_client()
        try:
            client.create_bank(
                bank_id=settings.bank_id,
                name="RecallDesk Support",
                mission=MISSION,
                directives=DIRECTIVES,
                disposition=DISPOSITION,
            )
            logger.info("Hindsight bank %r ready", settings.bank_id)
        except Exception as exc:  # bank may already exist
            logger.debug("create_bank returned (%s) — continuing", exc)

    # -- core ops ----------------------------------------------------------
    def retain_interaction(
        self,
        customer_email: str,
        role: str,
        text: str,
        *,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        client = self._ensure_client()
        payload_meta = {"customer_email": customer_email, **(metadata or {})}
        try:
            client.retain(
                bank_id=settings.bank_id,
                content=f"[{role}] {customer_email}: {text}",
                context="support chat",
                document_id=document_id,
                metadata=payload_meta,
                retain_async=False,
            )
        except Exception:
            logger.exception("Retain failed for %s", customer_email)
            # Never fail a live conversation because memory write hiccuped.

    def recall(self, query: str, max_tokens: Optional[int] = None, types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        client = self._ensure_client()
        try:
            response = client.recall(
                bank_id=settings.bank_id,
                query=query,
                max_tokens=max_tokens or settings.max_recall_tokens,
                types=types,
            )
        except Exception:
            logger.exception("Recall failed")
            return []
        results = getattr(response, "results", None) or []
        return [
            {
                "text": r.text,
                "type": getattr(r, "type", "world"),
                "score": float(getattr(r, "score", 0.0) or 0.0),
            }
            for r in results
        ]

    def reflect(self, query: str, context: Optional[str] = None) -> str:
        client = self._ensure_client()
        try:
            answer = client.reflect(bank_id=settings.bank_id, query=query, context=context, budget="mid")
            return getattr(answer, "text", "") or ""
        except Exception:
            logger.exception("Reflect failed")
            return ""

    # -- introspection ------------------------------------------------------
    def list_memories(self, search_query: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        client = self._ensure_client()
        try:
            items = client.list_memories(bank_id=settings.bank_id, search_query=search_query, limit=limit) or []
        except Exception:
            logger.exception("list_memories failed")
            return []
        return [
            {
                "id": str(getattr(m, "id", "")),
                "text": str(getattr(m, "text", "")),
                "type": str(getattr(m, "type", "world")),
                "created_at": str(getattr(m, "created_at", "")),
            }
            for m in items
        ]

    def list_mental_models(self) -> List[Dict[str, Any]]:
        client = self._ensure_client()
        try:
            models = client.list_mental_models(bank_id=settings.bank_id) or []
        except Exception:
            logger.exception("list_mental_models failed")
            return []
        return [
            {
                "id": str(getattr(mm, "id", "")),
                "name": str(getattr(mm, "name", "")),
                "text": str(getattr(mm, "text", "")),
                "updated_at": str(getattr(mm, "updated_at", getattr(mm, "created_at", ""))),
            }
            for mm in models
        ]

    def upsert_mental_model(self, name: str, text: str) -> None:
        client = self._ensure_client()
        try:
            client.create_mental_model(bank_id=settings.bank_id, name=name, text=text)
        except Exception:
            logger.exception("create_mental_model failed for %s", name)

    def bank_stats(self) -> Dict[str, int]:
        client = self._ensure_client()
        stats = {"memories": 0, "observations": 0, "mental_models": 0}
        try:
            for m in client.list_memories(bank_id=settings.bank_id, limit=1000) or []:
                stats["memories"] += 1
                if str(getattr(m, "type", "")) == "observation":
                    stats["observations"] += 1
            stats["mental_models"] = len(self.list_mental_models())
        except Exception:
            logger.exception("bank_stats failed")
        return stats

    def health(self) -> bool:
        try:
            client = self._ensure_client()
            client.get_version()
            return True
        except Exception:
            return False


hindsight_layer = HindsightLayer()
