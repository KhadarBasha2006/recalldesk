"""RecallDesk configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    # Groq / LLM
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_model: str = field(default_factory=lambda: os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"))
    groq_base_url: str = field(default_factory=lambda: os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"))

    # Hindsight
    hindsight_base_url: str = field(default_factory=lambda: os.getenv("HINDSIGHT_BASE_URL", "http://localhost:8888"))
    hindsight_api_key: str = field(default_factory=lambda: os.getenv("HINDSIGHT_API_KEY", ""))
    bank_id: str = field(default_factory=lambda: os.getenv("BANK_ID", "recalldesk-demo"))

    # Agent
    default_use_memory: bool = field(default_factory=lambda: _bool_env("USE_MEMORY", True))
    max_recall_tokens: int = field(default_factory=lambda: int(os.getenv("MAX_RECALL_TOKENS", "2048")))
    max_tool_iterations: int = field(default_factory=lambda: int(os.getenv("MAX_TOOL_ITERATIONS", "4")))
    request_timeout: float = field(default_factory=lambda: float(os.getenv("REQUEST_TIMEOUT", "60")))

    # CORS
    cors_origins: str = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"))

    # Demo fallbacks: run the full flow without external services.
    allow_mock_hindsight: bool = field(default_factory=lambda: _bool_env("ALLOW_MOCK_HINDSIGHT", True))
    allow_mock_llm: bool = field(default_factory=lambda: _bool_env("ALLOW_MOCK_LLM", True))


settings = Settings()
