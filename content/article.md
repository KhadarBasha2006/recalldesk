# My support agent stopped asking customers to repeat themselves. Here's what changed.

> **Note before publishing:** replace bracketed placeholders, add screenshots where marked, and adjust the voice so it reads like *you*. Do **not** mention the hackathon anywhere (see content guide — it's disqualifying). ~1,300 words.

---

Last month our support agent asked a customer for her order number. It was the fourth time that year she'd been asked. She had two dead routers, one failed escalation, and a pending refund on file — and our "state-of-the-art" chatbot knew none of it.

The problem wasn't the model. The problem was that the model had no memory. Every session started from zero, so every session re-litigated history the company already owned.

I built [RecallDesk](https://github.com/KhadarBasha2006/recalldesk) to fix that. This post is about the design decision that mattered most: making memory the backbone of the agent rather than a search box on the side.

## What the system does

RecallDesk is a customer-support agent with three components:

- A **memory layer** — [Hindsight](https://github.com/vectorize-io/hindsight), a purpose-built agent memory system that stores facts, links them into an entity graph, and consolidates related facts into *observations* with evidence tracking.
- An **agent loop** — recall before reasoning, tools for ground truth, then a grounded answer.
- A **system of record** — plain SQLite-style tables for orders, tickets and refunds. The LLM never touches this directly; it goes through tools.

The full loop per customer message:

1. **Recall** — search the customer's entire history (facts + observations + learned plays) *before* the model sees anything.
2. **Reason** — the LLM decides, grounded in that memory, whether it needs a tool.
3. **Tools** — order lookups, ticket lookups, refund approval, escalation.
4. **Answer** — grounded in memory + tool output.
5. **Retain** — the turn is written back to the memory bank with customer and role metadata.

Every reply ships with the memories it used. The UI renders them as evidence chips, so "why did the agent say that?" is always answerable.

## The through-line: contradictions are the product

Here's the detail that sold me on Hindsight over a plain vector store.

Six weeks into the demo history, the customer's story contains a contradiction: her *original* router was replaced under warranty, and then the *replacement* also failed. A naive RAG setup retrieves both facts with equal confidence and lets the LLM sort it out — which it does badly, usually by hedging or picking the wrong one.

Hindsight handles this structurally. When facts are retained, related ones get consolidated into an **observation** that tracks the history:

```text
world  | Priya's original PowerHub (ORD-7741) failed within 12 months.   [superseded]
world  | Replacement unit ORD-8102 ALSO drops connection nightly.        [2 sources]
obs    | Priya has had two failed PowerHub P2 units; firmware NW-118
       | is the suspected root cause.                                    [resolved: device replaced]
```

The agent doesn't retrieve "a customer who had a router problem." It retrieves *the current state of the story*, with proof counts and timestamps, and can say "you've had two failed units, and here's what we know about why" — which is exactly what an angry customer needs to hear.

*(Screenshot: Memory Inspector showing a world fact, its superseding fact, and the consolidated observation.)*

## Learning plays, not just facts

The second thing memory buys is *policy that used to live in people's heads*.

Our best support lead had a rule she applied on every difficult call: **acknowledge the failed escalation before any troubleshooting**. That rule existed nowhere in the docs. With Hindsight **mental models** — curated summary memories the bank carries into every recall — it became a first-class artifact:

```python
hindsight_layer.upsert_mental_model(
    name="empathy-first-after-failed-escalation",
    text="When a customer has a prior failed escalation, acknowledge the "
         "missed callback FIRST, before any troubleshooting. Learned from "
         "ESC-2201 (Aug 2026).",
)
```

Now every future conversation — handled by any agent instance — starts with that play in context. The team's expertise stops walking out the door at 6 pm.

## Proof over vibes: the memory toggle

The most useful thing we built turned out to be a single boolean. One click switches the same agent into stateless mode: same model, same prompt, same tools — only `use_memory` flips.

Without memory: *“I'm sorry to hear that. Could you share your order number and describe the issue?”*
With memory: *“Priya — I know this is your second PowerHub and the replacement is still dropping at 2am. That's tracked as firmware issue NW-118. I'm not asking you to diagnose anything; here's what I can do right now.”*

That's the whole pitch, in ten seconds, and it's measurable: replies carry latency, tool calls and the exact memories consulted.

*(Screenshot: the two replies side by side with the Memory OFF badge visible.)*

## Failure modes we designed for

Two things bite every LLM agent, so we handled them up front:

- **Function-calling flakiness.** Tool calls arrive with malformed JSON or wrong arity more often than anyone admits. The parser tolerates both — malformed arguments become an empty dict, wrong arity becomes a structured error the model can recover from, and the loop is hard-capped so nothing spins.
- **Memory outages.** A retain failure logs and continues; a recall failure returns an empty context and the agent says so honestly. Support chat must not 500 because the memory bank hiccuped.

## What I'd do differently

1. **Ground truth vs. memory should be a hard boundary from day one.** Early on the model happily quoted order data from memory. Moving all record reads behind tools made hallucinated order numbers structurally impossible.
2. **Show receipts in the UI.** Once memories were visible as chips, trust in the system's answers went up immediately — and debugging got trivial.
3. **Observations need feeding.** Consolidation is only as good as retention hygiene. Timestamped, well-contextualized retain calls are what make the contradiction resolution actually work.
4. **The toggle is the demo.** If you're building memory-powered anything, build the OFF switch early. It's the fastest way to see what the memory is actually buying you.

The next step is connecting the same bank to real email tickets, so the agent walks into every conversation with six months of context instead of six chats.

If you want to poke at the code: [RecallDesk on GitHub](https://github.com/KhadarBasha2006/recalldesk). The memory layer is [Hindsight](https://hindsight.vectorize.io/) — [agent memory](https://vectorize.io/what-is-agent-memory) that retains, recalls, and reflects.
