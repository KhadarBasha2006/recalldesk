"""Synthetic-but-realistic operational data (the "system of record").

The problem statement is explicit: *the #1 thing that makes a project look real
is the data.*  These records are used by the agent's tools; the *history* of how
they came to be lives in Hindsight memory (see scripts/seed_history.py).
"""
from __future__ import annotations

from typing import Any, Dict, List

ORDERS: Dict[str, Dict[str, Any]] = {
    "ORD-7741": {
        "order_id": "ORD-7741",
        "email": "priya.sharma@fastmail.com",
        "item": "Acme Cloud PowerHub P2 (mesh router)",
        "price": 189.00,
        "currency": "USD",
        "status": "delivered",
        "ordered_at": "2026-08-02",
        "delivered_at": "2026-08-06",
        "warranty_until": "2027-08-06",
    },
    "ORD-8102": {
        "order_id": "ORD-8102",
        "email": "priya.sharma@fastmail.com",
        "item": "Acme Cloud PowerHub replacement unit (warranty)",
        "price": 0.00,
        "currency": "USD",
        "status": "delivered",
        "ordered_at": "2026-08-14",
        "delivered_at": "2026-08-18",
        "warranty_until": "2027-08-18",
    },
    "ORD-8460": {
        "order_id": "ORD-8460",
        "email": "james.okafor@brightloop.io",
        "item": "Acme Cloud Business Gateway + 5 seats",
        "price": 1240.00,
        "status": "delivered",
        "ordered_at": "2026-09-01",
        "delivered_at": "2026-09-04",
        "currency": "USD",
        "warranty_until": "2027-09-04",
    },
}

TICKETS: Dict[str, Dict[str, Any]] = {
    "TCK-1043": {
        "ticket_id": "TCK-1043",
        "email": "priya.sharma@fastmail.com",
        "subject": "PowerHub drops connection every night",
        "status": "open",
        "created_at": "2026-09-19",
        "priority": "high",
        "related_order": "ORD-8102",
        "notes": "Replacement unit also dropping connection between 02:00-03:00. Escalated to network team.",
    },
    "ESC-2201": {
        "ticket_id": "ESC-2201",
        "email": "priya.sharma@fastmail.com",
        "subject": "Escalation: no callback after promise",
        "status": "closed-escalated",
        "created_at": "2026-08-21",
        "priority": "urgent",
        "related_order": "ORD-7741",
        "notes": "Customer waited 6 days for a promised callback that never came.",
    },
    "TCK-1102": {
        "ticket_id": "TCK-1102",
        "email": "james.okafor@brightloop.io",
        "subject": "SLA breach on September invoice",
        "status": "open",
        "created_at": "2026-09-12",
        "priority": "high",
        "related_order": "ORD-8460",
        "notes": "Business customer claims 99.2% uptime vs 99.9% SLA; wants credit.",
    },
}

REFUNDS: List[Dict[str, Any]] = [
    {
        "refund_id": "REF-3301",
        "order_id": "ORD-7741",
        "email": "priya.sharma@fastmail.com",
        "amount": 189.00,
        "status": "pending",
        "reason": "Original PowerHub failed within 12 months",
        "requested_at": "2026-09-20",
    }
]

CUSTOMER_PLANS: Dict[str, str] = {
    "priya.sharma@fastmail.com": "Pro",
    "james.okafor@brightloop.io": "Enterprise Pro",
    "elena.rossi@lumenpark.co": "Free",
}


def orders_for(email: str) -> List[Dict[str, Any]]:
    return [o for o in ORDERS.values() if o["email"] == email]


def tickets_for(email: str) -> List[Dict[str, Any]]:
    return [t for t in TICKETS.values() if t["email"] == email]


def refunds_for(email: str) -> List[Dict[str, Any]]:
    return [r for r in REFUNDS if r["email"] == email]
