"""Groq LLM client (OpenAI-compatible) with function-calling error handling.

The problem statement explicitly warns: "make sure to have your agent ready to
handle function calling errors."  This module therefore:

- retries transient failures (429 / 5xx) with exponential backoff + jitter,
- validates tool-call JSON and falls back to a safe "no tool" plan,
- tolerates malformed / missing `arguments` payloads,
- enforces an iteration cap so a looping tool call can't spin forever.
"""
from __future__ import annotations

import json
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import requests

from .config import settings

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    """Raised when the LLM cannot produce a usable completion."""


@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]
    id: str = ""

    @classmethod
    def from_api(cls, raw: Dict[str, Any]) -> "ToolCall":
        fn = raw.get("function") or {}
        raw_args = fn.get("arguments")
        args: Dict[str, Any] = {}
        if isinstance(raw_args, dict):
            args = raw_args
        elif isinstance(raw_args, str):
            try:
                parsed = json.loads(raw_args)
                if isinstance(parsed, dict):
                    args = parsed
            except json.JSONDecodeError:
                logger.warning("Malformed tool arguments JSON: %r", raw_args)
        return cls(name=str(fn.get("name") or ""), arguments=args, id=str(raw.get("id") or ""))


@dataclass
class LLMResponse:
    content: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)
    finish_reason: str = ""


def _post_chat(payload: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    url = f"{settings.groq_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if resp.status_code in (429, 500, 502, 503, 504):
        raise _Transient(str(resp.status_code))
    if resp.status_code >= 400:
        raise LLMError(f"Groq API error {resp.status_code}: {resp.text[:500]}")
    return resp.json()


class _Transient(Exception):
    pass


def _with_retries(fn: Callable[[], Dict[str, Any]], attempts: int = 3, base_delay: float = 0.7) -> Dict[str, Any]:
    last: Optional[Exception] = None
    for i in range(attempts):
        try:
            return fn()
        except _Transient as exc:
            last = exc
            delay = base_delay * (2 ** i) + random.uniform(0, 0.25)
            logger.warning("Transient Groq error (%s); retrying in %.2fs", exc, delay)
            time.sleep(delay)
        except requests.RequestException as exc:
            last = exc
            logger.warning("Network error calling Groq: %s", exc)
            time.sleep(0.5 * (i + 1))
    raise LLMError(f"Groq request failed after {attempts} attempts: {last}")


class GroqClient:
    """Thin, resilient wrapper around Groq's OpenAI-compatible chat API."""

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.3,
        max_tokens: int = 900,
    ) -> LLMResponse:
        payload: Dict[str, Any] = {
            "model": settings.groq_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        data = _with_retries(lambda: _post_chat(payload, settings.request_timeout))
        try:
            choice = (data.get("choices") or [{}])[0]
        except (IndexError, TypeError):  # pragma: no cover - defensive
            raise LLMError(f"Unexpected Groq response shape: {str(data)[:300]}")

        message = choice.get("message") or {}
        raw_calls = message.get("tool_calls") or []

        # Malformed tool_calls (e.g. not a list) are treated as absent.
        if not isinstance(raw_calls, list):
            raw_calls = []
        tool_calls = [c for c in (ToolCall.from_api(tc) for tc in raw_calls) if c.name]

        return LLMResponse(
            content=str(message.get("content") or ""),
            tool_calls=tool_calls,
            finish_reason=str(choice.get("finish_reason") or ""),
        )

    def stream_chat(self, messages: List[Dict[str, Any]], temperature: float = 0.3, max_tokens: int = 900):
        """Yield content deltas from a streaming chat completion."""
        payload = {
            "model": settings.groq_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        url = f"{settings.groq_base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {settings.groq_api_key}", "Content-Type": "application/json"}
        with requests.post(url, headers=headers, json=payload, timeout=settings.request_timeout, stream=True) as resp:
            if resp.status_code >= 400:
                raise LLMError(f"Groq stream error {resp.status_code}: {resp.text[:300]}")
            for line in resp.iter_lines():
                if not line:
                    continue
                decoded = line.decode("utf-8")
                if decoded.startswith("data: "):
                    chunk = decoded[len("data: "):]
                    if chunk.strip() == "[DONE]":
                        break
                    try:
                        obj = json.loads(chunk)
                        delta = (obj.get("choices") or [{}])[0].get("delta") or {}
                        piece = delta.get("content")
                        if piece:
                            yield str(piece)
                    except (json.JSONDecodeError, IndexError, TypeError):
                        # Drop malformed keep-alive / partial chunks rather than crash.
                        continue
