"""Node 3: write a reply grounded in retrieved text and order data."""
from langchain_core.output_parsers import StrOutputParser

from app.llm import get_llm
from app.prompts import DRAFT_PROMPT


def format_context(docs: list[dict]) -> str:
    if not docs:
        return "(none)"
    return "\n\n".join(f"[{d['source']}] {d['content']}" for d in docs)


def format_order(order: dict | None) -> str:
    if not order:
        return "(no order details)"
    return ", ".join(f"{k}: {v}" for k, v in order.items())


def generate_draft(state) -> str:
    chain = DRAFT_PROMPT | get_llm() | StrOutputParser()
    return chain.invoke({
        "ticket": state["ticket"],
        "order": format_order(state.get("order_info")),
        "context": format_context(state.get("docs", [])),
    })


def draft_node(state):
    return {"draft": generate_draft(state)}
