"""Final node: persist the outcome for the metrics tab and evaluation."""
from contextlib import closing

from langchain_core.runnables import RunnableConfig

from app import db


def log_node(state, config: RunnableConfig):
    db.init_db()
    thread_id = config.get("configurable", {}).get("thread_id", "")
    with closing(db.get_conn()) as conn:
        conn.execute(
            """INSERT INTO ticket_log (thread_id, ticket, category, urgency, sentiment,
               confidence, route, status, human_decision, final_reply, reasons)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                thread_id, state["ticket"], state.get("category"), state.get("urgency"),
                state.get("sentiment"), state.get("confidence"), state.get("route"),
                state.get("status"), state.get("human_decision"), state.get("final_reply"),
                "; ".join(state.get("reasons", [])),
            ),
        )
        conn.commit()
    return {}
