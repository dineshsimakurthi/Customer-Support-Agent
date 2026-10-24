"""Shared state passed between every node in the graph."""
from typing import Optional, TypedDict


class TicketState(TypedDict, total=False):
    # input
    ticket: str
    # classify
    category: str
    urgency: str
    sentiment: str
    order_id: Optional[str]
    # lookup / retrieve
    order_info: Optional[dict]
    docs: list[dict]
    # draft
    draft: str
    # confidence
    confidence: Optional[float]
    reasons: list[str]
    needs_human: bool
    # outcome
    human_decision: Optional[str]   # approve | edit | reject
    final_reply: str
    route: str                      # auto | human
    status: str                     # auto_sent | approved | edited | rejected
