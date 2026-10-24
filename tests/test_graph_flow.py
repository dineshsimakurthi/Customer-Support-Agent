"""End-to-end graph test with the LLM and vector store mocked out.

Proves: routing, the order-lookup branch, interrupt (pause) and resume, and logging.
"""
import sqlite3
from contextlib import closing

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app import config, db
from app.graph import build_graph
from app.schemas import Classification, ConfidenceResult


@pytest.fixture
def graph(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    with closing(db.get_conn()) as conn:
        conn.execute("INSERT INTO orders VALUES ('ORD-1001','A','Laptop',1299,'delivered','2026-01-01')")
        conn.execute("INSERT INTO orders VALUES ('ORD-1002','B','Headphones',89,'shipped','2026-01-01')")
        conn.commit()

    def fake_classify(ticket):
        return Classification(category="REFUND" if "refund" in ticket.lower() else "ACCOUNT",
                              urgency="medium", sentiment="neutral", reasoning="test")

    monkeypatch.setattr("app.nodes.classify.run_classifier", fake_classify)
    monkeypatch.setattr("app.nodes.retrieve.kb_search",
                        lambda *a, **k: [{"content": "30-day returns", "source": "refund_policy.md"}])
    monkeypatch.setattr("app.nodes.draft.generate_draft", lambda s: "Hello, here is your answer.")
    monkeypatch.setattr("app.nodes.confidence.rate_draft",
                        lambda s: ConfidenceResult(score=0.95, reasoning="well supported"))
    return build_graph(MemorySaver())


def cfg(tid):
    return {"configurable": {"thread_id": tid}}


def logged_rows():
    with closing(db.get_conn()) as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM ticket_log")]


def test_low_risk_ticket_is_auto_sent(graph):
    out = graph.invoke({"ticket": "How do I reset my password?"}, cfg("t1"))
    assert out["status"] == "auto_sent" and out["route"] == "auto"
    assert "__interrupt__" not in out
    assert logged_rows()[0]["status"] == "auto_sent"


def test_small_refund_with_order_lookup_is_auto_sent(graph):
    out = graph.invoke({"ticket": "Refund for ORD-1002 please"}, cfg("t2"))
    assert out["order_info"]["amount"] == 89.0
    assert out["status"] == "auto_sent"


def test_big_refund_pauses_then_resumes_on_approval(graph):
    out = graph.invoke({"ticket": "I want a refund for ORD-1001"}, cfg("t3"))
    assert "__interrupt__" in out                       # graph paused
    assert graph.get_state(cfg("t3")).next == ("human_review",)
    assert logged_rows() == []                          # nothing logged yet

    final = graph.invoke(Command(resume={"action": "approve"}), cfg("t3"))
    assert final["status"] == "approved" and final["final_reply"] == "Hello, here is your answer."
    assert logged_rows()[0]["human_decision"] == "approve"


def test_human_edit_and_reject(graph):
    graph.invoke({"ticket": "I want a refund for ORD-1001"}, cfg("t4"))
    final = graph.invoke(Command(resume={"action": "edit", "reply": "Custom reply"}), cfg("t4"))
    assert final["status"] == "edited" and final["final_reply"] == "Custom reply"

    graph.invoke({"ticket": "I want a refund for ORD-1001"}, cfg("t5"))
    final = graph.invoke(Command(resume={"action": "reject"}), cfg("t5"))
    assert final["status"] == "rejected" and final["final_reply"] == ""
