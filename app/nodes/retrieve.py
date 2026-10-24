"""Node 2b: retrieve policy rules + category-matched FAQ answers from the KB."""
from app.tools.kb_search import kb_search


def retrieve_node(state):
    query, category = state["ticket"], state.get("category")
    policies = kb_search(query, doc_type="policy", k=2)
    faqs = kb_search(query, category=category, doc_type="faq", k=3) if category else []
    if not faqs:  # fall back to any FAQ if the category filter returned nothing
        faqs = kb_search(query, doc_type="faq", k=3)
    return {"docs": policies + faqs}
