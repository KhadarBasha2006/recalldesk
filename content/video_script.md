# Demo Video Script (2–4 min, 1080p screen recording + voiceover)

> Before recording: start backend + frontend, run `python scripts/seed_history.py`, and increase font sizes. Close notifications.

---

## [0:00–0:30] Intro — on camera or over the home screen

> "Hi, I'm Shaik Adil from team Legacy Legends, and this is RecallDesk — a customer-support agent that remembers every interaction a customer has ever had with the company. It's built on Hindsight, an agent memory system, with Groq's gpt-oss-120b as the reasoning model."

**On screen:** the RecallDesk UI, Memory Inspector visible on the right showing seeded memories (60+), stats: memories / observations / plays.

## [0:30–1:00] The problem — Memory OFF

> "Here's the same agent with memory turned off. Ask about a nightly router issue…"

**On screen:** toggle 🚫 Memory OFF → send: *"My router keeps dropping every night again."*

> "It has no idea who Priya is. It asks for her order number, asks her to describe the problem she's described twice before, offers generic Wi-Fi advice. This is the stateless experience every customer hates."

## [1:00–2:30] The demo — Memory ON

**Toggle 🧠 Memory ON → send the same message.**

> "Same question, same model. Watch."

**Narrate while it streams:**
- Reply opens by acknowledging the *second* failed device and the missed escalation callback — learned play applied automatically.
- Evidence chips appear: *"recalled N memories"* — hover one: the observation about firmware NW-118.
- Memory Inspector updates live: two new memories (customer turn + agent turn).
- Send: *"Where is my refund?"* → tool chip `get_order` / refund context recalled; agent knows about the pending $189 refund without asking anything.
- Point at observations count increasing; mention consolidation: "the two 'device failed' facts were consolidated into one observation with proof counts — that's how it avoids contradicting itself."

## [2:30–3:15] The wrap

> "The whole difference is one boolean: memory on or off. Hindsight handles retain, recall, the entity graph, and observation consolidation — the agent just has to remember to look before it speaks. The thing that surprised me: the biggest win wasn't remembering facts, it was learning plays — our team's escalation playbook became a mental model every future conversation inherits."

> "Repo and article linked below. Thanks for watching."

---

## Title options for YouTube

1. My AI support agent never asks a customer to repeat themselves
2. Memory ON vs OFF: the demo that sells agent memory in 10 seconds
3. I gave a chatbot 6 weeks of customer history. Watch it work.
4. How Hindsight resolves contradictions my vector DB couldn't
5. The support agent that knows why you're angry before you speak

## Thumbnail prompt (Nano Banana / any image tool)

> "16:9 YouTube thumbnail. Split screen: left side dark and blurred — a generic chatbot saying 'Could you share your order number?'; right side vivid — a confident agent reply with glowing brain icon and memory chips. Big bold text: 'MEMORY: ON'. High contrast, tech-y, no stock-photo handshakes."
