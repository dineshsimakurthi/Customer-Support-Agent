"""Node 4: safety layer. Hard business rules first, then an LLM self-rating."""
from app import config
from app.llm import get_structured_llm
from app.nodes.draft import format_context, format_order
from app.prompts import CONFIDENCE_PROMPT
from app.schemas import ConfidenceResult


def apply_rules(state) -> list[str]:
    """Pure-Python risk rules. Any reason returned forces human review."""
    reasons = []
    if state.get("sentiment") == "angry":
        reasons.append("Customer is angry")
    if state.get("urgency") == "critical":
        reasons.append("Critical urgency")
    if not state.get("docs"):
        reasons.append("No knowledge base documents found")
    if state.get("order_id") and not state.get("order_info"):
        reasons.append(f"Order {state['order_id']} not found")
    order = state.get("order_info") or {}
    if state.get("category") == "REFUND" and order.get("amount", 0) > config.REFUND_LIMIT:
        reasons.append(
            f"Refund of ${order['amount']:.2f} exceeds ${config.REFUND_LIMIT:.0f} "
            "limit: manager approval required"
        )
    return reasons


def rate_draft(state) -> ConfidenceResult:
    chain = CONFIDENCE_PROMPT | get_structured_llm(ConfidenceResult)
    return chain.invoke({
        "ticket": state["ticket"],
        "order": format_order(state.get("order_info")),
        "context": format_context(state.get("docs", [])),
        "draft": state["draft"],
    })


def confidence_node(state):
    reasons = apply_rules(state)
    if reasons:  # hard rule hit: skip the extra LLM call, go straight to a human
        return {"confidence": None, "reasons": reasons, "needs_human": True}

    rating = rate_draft(state)
    if rating.score < config.CONFIDENCE_THRESHOLD:
        reasons.append(f"Low confidence ({rating.score:.2f}): {rating.reasoning}")
    return {"confidence": rating.score, "reasons": reasons, "needs_human": bool(reasons)}
