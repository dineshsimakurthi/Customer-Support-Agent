"""Node 2a: fetch order details when the ticket mentions an order ID."""
from app.tools.order_lookup import order_lookup


def lookup_order_node(state):
    info = order_lookup.invoke({"order_id": state["order_id"]})
    return {"order_info": info or None}
