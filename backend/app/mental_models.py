"""Learned support plays — the team's collective expertise as Hindsight mental models.

Each play was learned from real interactions (see content of scripts/seed_history.py).
During recall, these are surfaced so a *new* agent benefits from every past
conversation the team has had.
"""
from __future__ import annotations

from typing import Any, Dict, List

LEARNED_PLAYS: List[Dict[str, Any]] = [
    {
        "name": "empathy-first-after-failed-escalation",
        "text": (
            "When a customer has a prior failed escalation, acknowledge the missed callback FIRST, "
            "before any troubleshooting. Learned from ESC-2201 (Aug 2026): acknowledging the wait "
            "reduced tension immediately; jumping to diagnostics made it worse."
        ),
        "source_query": "How should the team open a conversation with a customer who has a prior failed escalation?",
    },
    {
        "name": "return-label-before-questions",
        "text": (
            "For hardware replacements, send the prepaid return label in the first reply — before "
            "asking any questions. Learned Sept 2026: customers with dead units need the path to "
            "resolution visible immediately."
        ),
        "source_query": "What is the team's process for hardware replacement requests?",
    },
    {
        "name": "nightly-disconnect-known-issue",
        "text": (
            "Nightly 02:00-03:00 disconnects on PowerHub units are a known firmware issue tracked as "
            "NW-118. Offer the beta firmware fix proactively; do not run generic Wi-Fi diagnostics first."
        ),
        "source_query": "What is known about nightly PowerHub disconnects and how should they be handled?",
    },
    {
        "name": "sla-credit-policy-business",
        "text": (
            "For Business/Enterprise SLA claims, pull the uptime report first, quote the exact measured "
            "uptime, and offer service credit per the 99.9% SLA schedule without being asked."
        ),
        "source_query": "How should Business and Enterprise SLA credit claims be handled?",
    },
]
