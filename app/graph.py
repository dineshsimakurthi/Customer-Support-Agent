"""Builds and compiles the LangGraph workflow. This is the heart of the project.

START -> classify -> (lookup_order) -> retrieve -> draft -> confidence
      -> auto_send | human_review (interrupt) -> log -> END
"""
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from app import config
from app.nodes.auto_send import auto_send_node
from app.nodes.classify import classify_node
from app.nodes.confidence import confidence_node
from app.nodes.draft import draft_node
from app.nodes.human_review import human_review_node
from app.nodes.log import log_node
from app.nodes.lookup_order import lookup_order_node
from app.nodes.retrieve import retrieve_node
from app.state import TicketState


def route_after_classify(state) -> str:
    if state.get("category") in config.ORDER_CATEGORIES and state.get("order_id"):
        return "lookup_order"
    return "retrieve"


def route_after_confidence(state) -> str:
    return "human_review" if state.get("needs_human") else "auto_send"


def build_graph(checkpointer=None):
    g = StateGraph(TicketState)
    g.add_node("classify", classify_node)
    g.add_node("lookup_order", lookup_order_node)
    g.add_node("retrieve", retrieve_node)
    g.add_node("draft", draft_node)
    g.add_node("confidence", confidence_node)
    g.add_node("auto_send", auto_send_node)
    g.add_node("human_review", human_review_node)
    g.add_node("log", log_node)

    g.add_edge(START, "classify")
    g.add_conditional_edges(
        "classify", route_after_classify,
        {"lookup_order": "lookup_order", "retrieve": "retrieve"},
    )
    g.add_edge("lookup_order", "retrieve")
    g.add_edge("retrieve", "draft")
    g.add_edge("draft", "confidence")
    g.add_conditional_edges(
        "confidence", route_after_confidence,
        {"human_review": "human_review", "auto_send": "auto_send"},
    )
    g.add_edge("auto_send", "log")
    g.add_edge("human_review", "log")
    g.add_edge("log", END)
    return g.compile(checkpointer=checkpointer)


def get_checkpointer() -> SqliteSaver:
    config.CHECKPOINT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.CHECKPOINT_DB_PATH, check_same_thread=False)
    return SqliteSaver(conn)


def get_graph():
    return build_graph(get_checkpointer())
