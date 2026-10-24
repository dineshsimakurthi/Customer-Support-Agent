"""Structured-data tool: look up an order in SQLite."""
from langchain_core.tools import tool

from app import db


@tool
def order_lookup(order_id: str) -> dict:
    """Return order details (product, amount, status, date) for an order ID, or {} if not found."""
    return db.get_order(order_id.strip().upper()) or {}
