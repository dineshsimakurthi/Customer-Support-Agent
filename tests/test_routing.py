"""Pure-Python tests of the safety rules and routing. No LLM or API key needed."""
from app import config
from app.graph import route_after_classify, route_after_confidence
from app.nodes.confidence import apply_rules

OK_DOC = [{"content": "x", "source": "refund_policy.md"}]


def base(**kw):
    s = {"ticket": "t", "category": "REFUND", "urgency": "medium",
         "sentiment": "neutral", "docs": OK_DOC}
    s.update(kw)
    return s


def test_clean_ticket_has_no_risk():
    assert apply_rules(base(category="ACCOUNT")) == []


def test_refund_over_limit_escalates():
    state = base(order_id="ORD-1001", order_info={"amount": config.REFUND_LIMIT + 1})
    assert any("manager approval" in r for r in apply_rules(state))


def test_refund_under_limit_is_fine():
    state = base(order_id="ORD-1002", order_info={"amount": 89.0})
    assert apply_rules(state) == []


def test_angry_and_critical_escalate():
    assert apply_rules(base(sentiment="angry"))
    assert apply_rules(base(urgency="critical"))


def test_missing_docs_or_unknown_order_escalate():
    assert apply_rules(base(docs=[]))
    assert apply_rules(base(order_id="ORD-9999", order_info=None))


def test_routing_functions():
    assert route_after_classify({"category": "REFUND", "order_id": "ORD-1001"}) == "lookup_order"
    assert route_after_classify({"category": "ACCOUNT", "order_id": None}) == "retrieve"
    assert route_after_classify({"category": "REFUND", "order_id": None}) == "retrieve"
    assert route_after_confidence({"needs_human": True}) == "human_review"
    assert route_after_confidence({"needs_human": False}) == "auto_send"
