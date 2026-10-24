"""Node 1: classify the ticket (category, urgency, sentiment) and pull out an order ID."""
import re

from app.llm import get_structured_llm
from app.prompts import CLASSIFY_PROMPT
from app.schemas import Classification

ORDER_ID_RE = re.compile(r"\bORD-\d{4,6}\b", re.IGNORECASE)


def run_classifier(ticket: str) -> Classification:
    chain = CLASSIFY_PROMPT | get_structured_llm(Classification)
    return chain.invoke({"ticket": ticket})


def classify_node(state):
    result = run_classifier(state["ticket"])
    match = ORDER_ID_RE.search(state["ticket"])
    return {
        "category": result.category,
        "urgency": result.urgency,
        "sentiment": result.sentiment,
        "order_id": match.group(0).upper() if match else None,
    }
