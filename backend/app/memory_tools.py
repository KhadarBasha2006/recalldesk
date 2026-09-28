"""Agent tools: ground-truth system-of-record operations.

The LLM never queries the database directly — it calls these tools.  Results
are returned as JSON strings ready to be appended to the conversation.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Dict

from . import mock_data

AUTO_REFUND_LIMIT = 200.00


def get_order(order_id: str) -> str:
    order = mock_data.ORDERS.get(order_id)
    if not order:
        return json.dumps({"error": f"Order {order_id} not found"})
    return json.dumps(order)


def list_orders(email: str) -> str:
    return json.dumps(mock_data.orders_for(email))


def get_ticket(ticket_id: str) -> str:
    ticket = mock_data.TICKETS.get(ticket_id)
    if not ticket:
        return json.dumps({"error": f"Ticket {ticket_id} not found"})
    return json.dumps(ticket)


def list_tickets(email: str) -> str:
    return json.dumps(mock_data.tickets_for(email))


def approve_refund(order_id: str, amount: float, reason: str) -> str:
    order = mock_data.ORDERS.get(order_id)
    if not order:
        return json.dumps({"error": f"Order {order_id} not found"})
    if amount > AUTO_REFUND_LIMIT:
        return json.dumps({
            "error": f"Amount ${amount:.2f} exceeds auto-approval limit of ${AUTO_REFUND_LIMIT:.2f}; escalate instead.",
            "requires_escalation": True,
        })
    refund = {
        "refund_id": f"REF-{3302 + len(mock_data.REFUNDS)}",
        "order_id": order_id,
        "email": order["email"],
        "amount": amount,
        "status": "approved",
        "reason": reason,
        "requested_at": "2026-09-28",
    }
    mock_data.REFUNDS.append(refund)
    return json.dumps(refund)


def escalate(ticket_id: str, reason: str, summary: str) -> str:
    ticket = mock_data.TICKETS.get(ticket_id)
    if not ticket:
        return json.dumps({"error": f"Ticket {ticket_id} not found"})
    ticket["status"] = "escalated"
    ticket["escalation_reason"] = reason
    ticket["escalation_summary"] = summary
    return json.dumps({"ok": True, "ticket_id": ticket_id, "status": "escalated", "queue": "Tier-2 network"})


TOOL_IMPLS: Dict[str, Callable[..., str]] = {
    "get_order": get_order,
    "list_orders": list_orders,
    "get_ticket": get_ticket,
    "list_tickets": list_tickets,
    "approve_refund": approve_refund,
    "escalate": escalate,
}
