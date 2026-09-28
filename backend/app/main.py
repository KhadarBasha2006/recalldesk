"""FastAPI application exposing the RecallDesk agent."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .agent import support_agent
from .config import settings
from .hindsight_layer import hindsight_layer
from .seed import run_seed

app = FastAPI(title="RecallDesk", version="1.0.0", description="Customer support agent with Hindsight memory")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    customer_email: str = "priya.sharma@fastmail.com"
    customer_name: str = "Priya Sharma"
    session_id: Optional[str] = None
    use_memory: bool = True


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "hindsight": hindsight_layer.health(),
        "model": settings.groq_model,
        "bank_id": settings.bank_id,
    }


@app.post("/api/chat")
def chat(req: ChatRequest) -> Dict[str, Any]:
    response = support_agent.respond(
        customer_email=req.customer_email,
        customer_name=req.customer_name,
        message=req.message,
        session_id=req.session_id,
        use_memory=req.use_memory,
    )
    return {
        "reply": response.reply,
        "memory_used": response.memory_used,
        "tool_calls": response.tool_calls,
        "latency_ms": response.latency_ms,
        "session_id": response.session_id,
        "used_memory": response.used_memory,
    }


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    import sse_starlette.sse as sse

    def event_gen():
        for event in support_agent.stream_respond(
            customer_email=req.customer_email,
            customer_name=req.customer_name,
            message=req.message,
            session_id=req.session_id,
            use_memory=req.use_memory,
        ):
            yield sse.ServerSentEvent(**event)

    return sse.EventSourceResponse(event_gen())


@app.get("/api/memory/stats")
def memory_stats() -> Dict[str, Any]:
    return hindsight_layer.bank_stats()


@app.get("/api/memory/search")
def memory_search(q: str = "", limit: int = 50) -> Dict[str, Any]:
    return {"memories": hindsight_layer.list_memories(search_query=q or None, limit=limit)}


@app.get("/api/memory/mental-models")
def mental_models() -> Dict[str, Any]:
    return {"mental_models": hindsight_layer.list_mental_models()}


@app.post("/api/memory/seed")
def memory_seed() -> Dict[str, Any]:
    run_seed()
    return {"ok": True, "detail": "Bank created and history seeded"}


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
