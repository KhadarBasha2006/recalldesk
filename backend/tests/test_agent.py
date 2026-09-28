from __future__ import annotations

import json

from tests.conftest import no_tool_reply, tool_call_response


def test_agent_uses_memory_and_cites_it(scripted_agent, fake_hindsight):
    agent = scripted_agent([no_tool_reply("Hi Priya — I know the replacement unit is still dropping at night.")])
    res = agent.respond(customer_email="priya.sharma@fastmail.com", customer_name="Priya Sharma", message="my router keeps dropping")

    assert "night" in res.reply
    assert res.used_memory is True
    assert len(res.memory_used) == 3
    # every turn is retained: user + agent
    retained_texts = [r["content"] for r in fake_hindsight.retained]
    assert any("customer" in t for t in retained_texts)
    assert any("agent" in t for t in retained_texts)


def test_agent_memory_off_skips_recall_and_retain(scripted_agent, fake_hindsight):
    agent = scripted_agent([no_tool_reply("I'm sorry, could you share your order number?")])
    res = agent.respond(
        customer_email="priya.sharma@fastmail.com",
        customer_name="Priya Sharma",
        message="where is my refund",
        use_memory=False,
    )

    assert res.used_memory is False
    assert res.memory_used == []
    assert fake_hindsight.retained == []


def test_agent_runs_tool_and_returns_answer(scripted_agent, fake_hindsight):
    agent = scripted_agent(
        [
            tool_call_response("get_order", {"order_id": "ORD-8102"}),
            no_tool_reply("Your replacement unit ORD-8102 was delivered on 2026-08-18."),
        ]
    )
    res = agent.respond(
        customer_email="priya.sharma@fastmail.com", customer_name="Priya", message="did my replacement arrive?"
    )

    assert res.tool_calls and res.tool_calls[0]["name"] == "get_order"
    assert res.tool_calls[0]["result"]["status"] == "delivered"
    assert "ORD-8102" in res.reply


def test_agent_survives_unknown_tool(scripted_agent, fake_hindsight):
    agent = scripted_agent(
        [
            tool_call_response("delete_universe", {}),
            no_tool_reply("Let's stay focused on your router."),
        ]
    )
    res = agent.respond(customer_email="x@y.z", customer_name="X", message="do something wild")
    assert res.tool_calls[0]["result"]["error"].startswith("Unknown tool")
    assert "router" in res.reply


def test_agent_survives_bad_tool_arguments(scripted_agent, fake_hindsight):
    # approve_refund requires 3 args; call with wrong arity
    agent = scripted_agent(
        [
            tool_call_response("approve_refund", {"order_id": "ORD-8102"}),
            no_tool_reply("Let me check that refund again."),
        ]
    )
    res = agent.respond(customer_email="p@x.y", customer_name="P", message="refund please")
    assert "error" in res.tool_calls[0]["result"]
    assert "refund" in res.reply.lower()


def test_agent_llm_failure_returns_fallback(scripted_agent, fake_hindsight):
    from app.llm import LLMError

    class Boom:
        def chat(self, *a, **k):
            raise LLMError("groq down")

        def stream_chat(self, *a, **k):
            raise LLMError("groq down")

    agent = SupportAgentWithBoom(Boom())
    res = agent.respond(customer_email="p@x.y", customer_name="P", message="hi")
    assert "specialist" in res.reply


def SupportAgentWithBoom(llm):
    from app.agent import SupportAgent

    return SupportAgent(llm=llm)


def test_tool_loop_gives_up_after_max_iterations(scripted_agent, fake_hindsight):
    from app.config import settings

    old = settings.max_tool_iterations
    settings.max_tool_iterations = 1
    try:
        agent = scripted_agent(
            [
                tool_call_response("list_orders", {"email": "p@x.y"}),
                tool_call_response("list_orders", {"email": "p@x.y"}),  # would loop
            ]
        )
        res = agent.respond(customer_email="p@x.y", customer_name="P", message="list my orders")
        assert "specialist" in res.reply
    finally:
        settings.max_tool_iterations = old


def test_refund_tool_enforces_limit():
    from app import memory_tools

    over = json.loads(memory_tools.approve_refund("ORD-7741", 5000.0, "test"))
    assert over["requires_escalation"] is True

    ok = json.loads(memory_tools.approve_refund("ORD-7741", 50.0, "goodwill credit"))
    assert ok["status"] == "approved"


def test_escalation_tool_marks_ticket():
    from app import memory_tools

    out = json.loads(memory_tools.escalate("TCK-1043", "recurring hardware fault", "Full history in memory bank."))
    assert out["ok"] is True
    from app.mock_data import TICKETS

    assert TICKETS["TCK-1043"]["status"] == "escalated"
