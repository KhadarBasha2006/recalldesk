<div align="center">

# 🧠 RecallDesk

**A customer-support agent with total recall — powered by [Hindsight](https://github.com/vectorize-io/hindsight) agent memory.**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-latest-green.svg)](https://fastapi.tiangolo.com/)
[![Hindsight](https://img.shields.io/badge/memory-Hindsight-7c3aed)](https://hindsight.vectorize.io/)
[![Groq](https://img.shields.io/badge/LLM-Groq-f55036)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

*No customer ever has to repeat their story twice.*

</div>

---

## The Problem

> *“Nothing angers a customer more than repeating their story.”*

A real support inbox mixes three things that chatbots handle badly:

1. **History that predates the bot.** The customer emailed three times last quarter,
   opened two tickets, and got a replacement charger — *before* they ever opened this chat.
2. **Facts that change.** A customer upgrades their plan; the old fact (“Free plan”)
   is now wrong, not deleted. Naive RAG happily retrieves the stale fact forever.
3. **Lessons the team learns on the job.** “Empathize first with customers who had a
   failed escalation” isn't in any doc — it lives in agents' heads and leaves with them.

A vanilla LLM chatbot sees none of it. A plain vector-store RAG bot sees it as
undifferentiated text blobs and can't resolve contradictions.

## What RecallDesk Does

RecallDesk is a **memory-first support agent** that:

- 🧠 **Retains every interaction** (chats, tickets, order events) into a Hindsight
  memory bank — facts are extracted, entities linked into a graph, and related facts
  are consolidated into **observations** (e.g., plan changes become a *superseded
  history*, not a contradiction).
- 🔎 **Recalls before it replies** — every answer is grounded in a multi-strategy
  memory search (semantic + keyword + graph + temporal) with citations.
- 📈 **Gets better with use** — support plays are learned over time and applied in
  later conversations, and every reply shows *why* (which memories it used, with
  proof counts and timestamps).
- 🎛 **Proves the value of memory live** — a one-click *Memory OFF* mode degrades the
  same agent into a stateless chatbot so you can see the difference in 10 seconds.

## Architecture

```
                                   ┌────────────────────────────────┐
                                   │        React (Vite) SPA        │
                                   │  Chat · Memory Inspector ·     │
                                   │  Memory ON/OFF · Stats         │
                                   └───────────────┬────────────────┘
                                                   │ REST / SSE
                                   ┌───────────────▼────────────────┐
                                   │      FastAPI backend :8000     │
                                   │  ┌────────────┐ ┌───────────┐  │
                                   │  │ Agent loop │ │  Tools    │  │
                                   │  │ recall →   │ │ · orders  │  │
                                   │  │ reason →   │ │ · tickets │  │
                                   │  │ tool →     │ │ · refund  │  │
                                   │  │ answer     │ │ · escalate│  │
                                   │  └─────┬──────┘ └─────┬─────┘  │
                                   │        │              │        │
                                   │  ┌─────▼──────────────▼─────┐  │
                                   │  │        Groq LLM          │  │
                                   │  │ gpt-oss-120b (function   │  │
                                   │  │ calling, with retries)   │  │
                                   │  └──────────────────────────┘  │
                                   └───────┬──────────────┬─────────┘
                                           │              │
                        ┌──────────────────▼───┐   ┌──────▼──────────────────┐
                        │  Hindsight :8888     │   │  SQLite                 │
                        │  retain / recall /   │   │  orders · tickets ·     │
                        │  reflect / banks     │   │  refunds (ground truth) │
                        └──────────────────────┘   └─────────────────────────┘
```

**Why the LLM never touches the database:** the agent answers *only* from memory,
and uses tools for ground-truth system-of-record data. Memory supplies the story
(history, preferences, outcomes, learned plays); tools supply the numbers. When
memory and tools disagree (customer says one thing, DB says another), the agent
flags the conflict instead of guessing — exactly the behavior you want when a
customer disputes a delivery date.

## How Hindsight Memory Is Used (the 25%)

Memory is not a bolt-on; **it is the product**. Concretely:

| Capability | Hindsight feature | Where |
|---|---|---|
| Every turn is remembered, with timestamps & source docs | `retain()` (facts + entities + graph) | `hindsight_layer.py` → `retain_interaction()` |
| Answers are grounded in past history with citations | `recall()` (TEMPR: semantic+keyword+graph+temporal) | `agent.py` → `_recall_context()` |
| Plan changes become observations with proof counts and resolved conflicts — not contradictions | Observation consolidation | Automatic inside Hindsight; surfaced in the UI and in `stats()` |
| The agent's persona & hard rules live in the bank | `create_bank(mission=…, directives=[…])` | `hindsight_layer.py` → `ensure_bank()` |
| Learned support plays (what works for this team) persist across conversations | Bank **mental models** (curated summary memories) | `mental_models.py`, `MemoryInspector` |
| Senior-agent reasoning for escalation summaries | `reflect()` — mission + disposition aware | `agent.py` → `_hindsight_reflect()` |
| Memory quality is observable | Bank stats: memory counts, observations, mental models | `/api/memory/stats`, Stats tab |

### The demo in one sentence
> Seed 6 weeks of history for one customer, turn memory **off** (generic apologies,
> re-asks for the order number, no empathy), turn memory **on** (instant greeting by
> name, correct order + plan + prior failure, the exact play the team learned), then
> tell the agent something new and watch the Memory Inspector update with a fresh
> fact — and, after consolidation, a new observation.

### Design decisions that make the memory visible

- **A dedicated Memory Inspector tab** streams everything the bank knows:
  memories (facts/observations) and mental models, searchable, with type and
  timestamp chips.
- **The Memory OFF toggle** is the story: same question, same model, same prompt —
  the only variable is memory.
- **The agent shows its receipts.** Every reply carries `memory_used` with the
  recalled texts, types, and recency, and the UI renders them as evidence chips.

## Quickstart

### 1. Run Hindsight

```bash
docker run -it --pull always --name hindsight --restart unless-stopped \
  --shm-size=1g -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=groq \
  -e HINDSIGHT_API_LLM_API_KEY=$GROQ_API_KEY \
  -e HINDSIGHT_API_LLM_MODEL=openai/gpt-oss-120b \
  ghcr.io/vectorize-io/hindsight:latest
```

API: http://localhost:8888 · Control plane (UI): http://localhost:9999

> No Docker? `pip install hindsight-api` and run `hindsight-api` with the same env vars.
> Or use [Hindsight Cloud](https://ui.hindsight.vectorize.io) (promo `MEMHACK99` for $50 credits) —
> point `HINDSIGHT_BASE_URL` at your cloud instance and set `HINDSIGHT_API_KEY`.

### 2. Configure & run the backend

```bash
cp .env.example .env                 # add GROQ_API_KEY (free at groq.com)
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/seed_history.py       # create the bank + seed 6 weeks of history
uvicorn app.main:app --reload --port 8000
```

### 3. Run the frontend

```bash
cd frontend
npm install && npm run dev           # http://localhost:5173
```

### 4. Seed data & demo flow

`scripts/seed_history.py` creates realistic, customer-specific history:

- **Priya Sharma** — customer since 2025. Pro plan, two prior tickets (charger
  failure → replacement), one failed escalation (case `ESC-2201`), a refund
  request for the replacement unit, and a strong preference for email.
- **James Okafor** — business customer, Ent Pro plan, SLA dispute.
- **Elena Rossi** — the support team's learned plays: empathy-first after failed
  escalation, always include the return label *before* asking for details, etc.

Then run the 3-step demo from `DEMO_SCRIPT.md` (≈ 2 minutes).

## Project Structure

```
hindsight_support_agent/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + routes + SSE
│   │   ├── agent.py             # memory-first agent loop (recall→reason→tools→retain)
│   │   ├── llm.py               # Groq client, function-calling with error handling
│   │   ├── hindsight_layer.py   # retain/recall/reflect wrappers + bank config
│   │   ├── mental_models.py     # learned-support-play mental models
│   │   ├── memory_tools.py      # agent tools: orders, tickets, refunds, escalation
│   │   ├── mock_data.py         # synthetic-but-realistic customers/tickets/orders
│   │   └── config.py            # settings from environment
│   ├── tests/                   # pytest suite (Hindsight + Groq mocked)
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/                    # React + Vite + Tailwind SPA
├── scripts/seed_history.py      # creates the bank + history
├── content/                     # article, social post, reddit post, video script
├── docker-compose.yml
├── .github/workflows/ci.yml
├── LICENSE
└── SUBMISSION_CHECKLIST.md
```

## Testing

```bash
cd backend && pytest -v
```

The suite mocks the Hindsight client and Groq, and covers the agent loop
(memory used vs not), the memory layer wrappers, the tools, and the API routes —
including the SSE streaming path. CI runs it on every push.

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat` | Send a customer message; returns reply + `memory_used` + tool calls |
| `POST` | `/api/chat/stream` | Same, but streams tokens via SSE |
| `GET` | `/api/memory/stats` | Bank statistics (memories, observations, mental models) |
| `GET` | `/api/memory/search` | Search everything the bank knows (Inspector) |
| `GET` | `/api/memory/mental-models` | The support plays the agent has learned |
| `POST` | `/api/memory/seed` | Create the bank and seed history (idempotent) |
| `GET` | `/api/health` | Backend + Hindsight health |

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | — | LLM for the agent (and for Hindsight's own extraction) |
| `HINDSIGHT_BASE_URL` | `http://localhost:8888` | Hindsight API |
| `HINDSIGHT_API_KEY` | — | Only for Hindsight Cloud |
| `BANK_ID` | `recalldesk-demo` | Memory bank id |
| `USE_MEMORY` | `true` | Default memory mode (toggleable at runtime) |

## Team

Built by **Team [your-team-name]** for the *AI Agents That Learn Using Hindsight* track.

- [Your Name] — backend & memory integration
- [Teammate] — frontend & demo
- [Teammate] — content & testing

## License

MIT — see [LICENSE](LICENSE).