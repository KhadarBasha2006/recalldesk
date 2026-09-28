from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import no_tool_reply


def test_health_endpoint(fake_hindsight):
    client = TestClient(app)
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["hindsight"] is True


def test_chat_endpoint_with_memory(fake_hindsight, monkeypatch):
    from app.agent import SupportAgent
    from tests.conftest import ScriptedGroq

    monkeypatch.setattr(
        "app.main.support_agent",
        SupportAgent(llm=ScriptedGroq([no_tool_reply("Hi Priya, I remember the escalation.")])),
    )
    client = TestClient(app)
    res = client.post(
        "/api/chat",
        json={
            "message": "you there?",
            "customer_email": "priya.sharma@fastmail.com",
            "customer_name": "Priya Sharma",
            "use_memory": True,
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert "escalation" in body["reply"]
    assert len(body["memory_used"]) == 3
    assert body["used_memory"] is True


def test_memory_endpoints(fake_hindsight):
    client = TestClient(app)
    assert client.get("/api/memory/stats").json()["memories"] == 4
    assert len(client.get("/api/memory/search?q=priya").json()["memories"]) > 0
    mm = client.get("/api/memory/mental-models").json()["mental_models"]
    assert isinstance(mm, list)


def test_seed_endpoint(fake_hindsight):
    client = TestClient(app)
    res = client.post("/api/memory/seed")
    assert res.status_code == 200
    assert res.json()["ok"] is True
