# Reddit Post (submit as a **Link post** to your published article)

> Pick ONE subreddit: r/llmdevs, r/sideproject, r/aiagents, or r/aimemory.
> No mention of the event anywhere. Title and body must stand on their own.

---

**Title options (pick one):**

1. I built a support agent that never asks customers to repeat themselves — Hindsight memory, receipts included
2. Show HN-style: my agent answers from 6 weeks of customer history before the customer finishes typing
3. Vector search kept retrieving contradictions, so I switched to Hindsight's observation consolidation
4. The boolean that made my AI agent demo obvious: memory ON vs memory OFF
5. Function calling failed more than my model did — here's how I hardened the tool loop

**Body (paste as the link post's text or first comment):**

Built a customer-support agent where memory is the backbone, not a feature:

- Every turn is retained with timestamps into a Hindsight bank (facts → entity graph → consolidated observations)
- Recall runs before the LLM sees the message, and the UI shows the exact memories used as evidence chips
- Contradictions ("device failed" vs "device was replaced") resolve into observations with proof counts instead of both facts floating around
- Team playbooks live as mental models, so learned behavior persists across conversations
- Ground truth (orders/tickets/refunds) is behind function-calling tools — the model physically cannot quote a made-up order number

Stack: Python + FastAPI, Groq (openai/gpt-oss-120b), Hindsight for memory, React frontend with a live Memory Inspector.

Happy to answer questions about the memory design — especially the contradiction handling and the tool-call error hardening.

Repo: https://github.com/KhadarBasha2006/recalldesk
Article: [your article link]
