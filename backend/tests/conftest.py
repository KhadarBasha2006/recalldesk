"""Shared fixtures: Hindsight and Groq are always mocked in tests."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.agent import SupportAgent  # noqa: E402
from app.hindsight_layer import HindsightLayer  # noqa: E402
from app.llm import LLMResponse, ToolCall  # noqa: E402


@dataclass
class FakeMemory:
    id: str = ""
    text: str = ""
    type: str = "world"
    created_at: str = "2026-09-01T00:00:00"
    score: float = 0.9


@dataclass
class FakeRecallResponse:
    results: List[FakeMemory] = field(default_factory=list)


@dataclass
class FakeReflectResponse:
    text: str = "Grounded answer from memory."


class FakeHindsightClient:
    """Drop-in stand-in for hindsight_client.Hindsight."""

    def __init__(self) -> None:
        self.retained: List[Dict[str, Any]] = []
        self.banks: List[str] = []
        self.models: Dict[str, List[FakeMemory]] = {}

    # core
    def create_bank(self, bank_id: str, **_: Any) -> None:
        self.banks.append(bank_id)

    def retain(self, bank_id: str, content: str, **kwargs: Any) -> None:
        self.retained.append({"bank_id": bank_id, "content": content, **kwargs})

    def recall(self, bank_id: str, query: str, **_: Any) -> FakeRecallResponse:
        return FakeRecallResponse(
            results=[
                FakeMemory(id="m1", text="Priya's replacement PowerHub (ORD-8102) also drops connection nightly.", type="world"),
                FakeMemory(id="m2", text="Priya had a failed escalation ESC-2201: a promised callback never happened.", type="world"),
                FakeMemory(id="m3", text="Team play: acknowledge the failed escalation first, then troubleshoot.", type="observation"),
            ]
        )

    def reflect(self, bank_id: str, query: str, **_: Any) -> FakeReflectResponse:
        return FakeReflectResponse()

    # introspection
    def list_memories(self, bank_id: str, search_query: str | None = None, limit: int = 100, **_: Any) -> List[FakeMemory]:
        return [
            FakeMemory(id="m1", text="Priya's replacement PowerHub also drops connection nightly.", type="world"),
            FakeMemory(id="m2", text="Priya had a failed escalation ESC-2201.", type="world"),
            FakeMemory(id="m3", text="Team play: acknowledge escalation failures first.", type="observation"),
            FakeMemory(id="m4", text="I suggested the beta firmware for NW-118.", type="experience"),
        ]

    def list_mental_models(self, bank_id: str) -> List[FakeMemory]:
        return self.models.get(bank_id, [])

    def create_mental_model(self, bank_id: str, name: str, source_query: str, id: str | None = None) -> None:
        self.models.setdefault(bank_id, []).append(FakeMemory(id=id or name, text=source_query, type="mental_model"))

    def get_version(self) -> Dict[str, str]:
        return {"api_version": "test"}


@pytest.fixture()
def fake_hindsight(monkeypatch: pytest.MonkeyPatch) -> FakeHindsightClient:
    client = FakeHindsightClient()
    layer = HindsightLayer()
    layer._client = client
    monkeypatch.setattr("app.agent.hindsight_layer", layer)
    monkeypatch.setattr("app.main.hindsight_layer", layer)
    return client


class ScriptedGroq:
    """Groq double that replays scripted LLM responses."""

    def __init__(self, responses: List[LLMResponse]) -> None:
        self.responses = list(responses)
        self.calls: List[List[Dict[str, Any]]] = []

    def chat(self, messages: List[Dict[str, Any]], tools: Any = None, **_: Any) -> LLMResponse:
        self.calls.append(messages)
        if not self.responses:
            return LLMResponse(content="default reply", tool_calls=[], finish_reason="stop")
        return self.responses.pop(0)

    def stream_chat(self, messages: List[Dict[str, Any]], **_: Any):
        yield "scripted "


@pytest.fixture()
def scripted_agent(fake_hindsight: FakeHindsightClient) -> callable:  # type: ignore[valid-type]
    def _make(responses: List[LLMResponse]) -> SupportAgent:
        return SupportAgent(llm=ScriptedGroq(responses))

    return _make


def no_tool_reply(content: str) -> LLMResponse:
    return LLMResponse(content=content, tool_calls=[], finish_reason="stop")


def tool_call_response(name: str, args: Dict[str, Any]) -> LLMResponse:
    return LLMResponse(
        content="",
        tool_calls=[ToolCall(name=name, arguments=args, id="call_1")],
        finish_reason="tool_calls",
    )
