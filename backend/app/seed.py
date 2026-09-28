"""Create the Hindsight bank and seed six weeks of realistic customer history.

Idempotent-ish: safe to re-run; it re-retains the same document ids so the bank
stays consistent.  Run via `python scripts/seed_history.py` or
`POST /api/memory/seed`.
"""
from __future__ import annotations

import logging
from datetime import datetime

from .config import settings
from .hindsight_layer import DIRECTIVES, DISPOSITION, MISSION, hindsight_layer
from .mental_models import LEARNED_PLAYS

logger = logging.getLogger(__name__)

# --- 6 weeks of Priya's history (the demo customer) ------------------------
PRIYA = ("Priya Sharma", "priya.sharma@fastmail.com")

PRIYA_HISTORY = [
    # (when, content)
    ("2026-08-02", "Order event: Priya Sharma ordered ORD-7741, an Acme Cloud PowerHub P2 mesh router, for $189.00."),
    ("2026-08-06", "Order event: ORD-7741 was delivered to Priya Sharma. She is on the Pro plan."),
    ("2026-08-19", "Priya reported her new PowerHub P2 (ORD-7741) drops its connection every night between 02:00 and 03:00. She was frustrated; this is her first Acme hardware."),
    ("2026-08-21", "Ticket TCK-1017 opened for Priya: nightly PowerHub disconnects. Support promised a callback within 48 hours."),
    ("2026-08-27", "The promised callback for Priya's ticket never happened. She emailed twice asking for status. Escalation ESC-2201 was opened — customer waited 6 days with no follow-up."),
    ("2026-08-30", "Priya told support: 'I spend 20 minutes every night rebooting this thing. I'm losing trust.' Agent apologized; no resolution offered. Contact preference: email, not phone."),
    ("2026-09-02", "Resolution: the original PowerHub (ORD-7741) was diagnosed as faulty. A warranty replacement was approved; return label sent. Priya asked for written confirmation by email for everything."),
    ("2026-09-14", "Replacement unit ORD-8102 delivered to Priya. Pro plan confirmed active. She thanked the team but reported the replacement ALSO drops connection nightly — same 02:00-03:00 window."),
    ("2026-09-19", "Ticket TCK-1043 opened for Priya: replacement PowerHub also disconnects nightly. Network team suspects firmware issue NW-118 affecting PowerHub P2 units."),
    ("2026-09-20", "Priya requested a refund for the replacement unit ORD-8102 ($189.00 pending, REF-3301). She said: 'I don't want a third device, I want working internet.'"),
    ("2026-09-25", "Learned outcome: for Priya, acknowledging the failed ESC-2201 escalation FIRST before troubleshooting made the conversation dramatically calmer. Store as a team play."),
]

JAMES = ("James Okafor", "james.okafor@brightloop.io")
JAMES_HISTORY = [
    ("2026-09-01", "Order event: James Okafor ordered ORD-8460, Acme Cloud Business Gateway with 5 seats, for $1,240.00."),
    ("2026-09-04", "Order event: ORD-8460 delivered. James is on the Enterprise Pro plan with a 99.9% uptime SLA."),
    ("2026-09-12", "Ticket TCK-1102: James reports measured uptime of 99.2% for September vs the 99.9% SLA. He wants service credit and is evaluating alternatives."),
]

ELENA = ("Elena Rossi", "elena.rossi@lumenpark.co")

# Elena plays the senior support lead who trains the agent (mental models).
ELENA_COACHING = [
    "Team play (from Elena's coaching): for any customer with a failed escalation in history, acknowledge the missed promise first, then troubleshoot.",
    "Team play: send the prepaid return label in the FIRST reply for hardware replacements, before asking anything.",
    "Team play: nightly 02:00-03:00 PowerHub disconnects = known firmware issue NW-118; offer beta firmware proactively, skip generic Wi-Fi diagnostics.",
]


def run_seed() -> None:
    hindsight_layer.ensure_bank()

    def seed_person(name: str, email: str, history: list[tuple[str, str]], doc_prefix: str) -> None:
        for i, (when, content) in enumerate(history, 1):
            hindsight_layer.retain_interaction(
                customer_email=email,
                role="history",
                text=f"[{when}] {content}",
                document_id=f"{doc_prefix}-{i:02d}",
                metadata={"seeded_on": datetime.now().isoformat()},
            )

    seed_person(*PRIYA, PRIYA_HISTORY, "priya-history")
    seed_person(*JAMES, JAMES_HISTORY, "james-history")

    for i, note in enumerate(ELENA_COACHING, 1):
        hindsight_layer.retain_interaction(
            customer_email=ELENA[1],
            role="team-lead",
            text=note,
            document_id=f"elena-plays-{i:02d}",
            metadata={"kind": "team-play"},
        )

    for play in LEARNED_PLAYS:
        hindsight_layer.upsert_mental_model(play["name"], play["source_query"])

    logger.info("Seeded bank %r", settings.bank_id)


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    run_seed()
