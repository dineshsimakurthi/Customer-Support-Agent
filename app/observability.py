"""Langfuse tracing. Everything here is optional and fails silently."""
from app import config


def get_handler():
    if not config.LANGFUSE_ENABLED:
        return None
    try:
        try:
            from langfuse.langchain import CallbackHandler      # langfuse v3
        except ImportError:
            from langfuse.callback import CallbackHandler       # langfuse v2
        return CallbackHandler()
    except Exception:
        return None


def make_run_config(thread_id: str, handler=None) -> dict:
    cfg = {
        "configurable": {"thread_id": thread_id},
        "metadata": {"langfuse_session_id": thread_id},  # groups a ticket's runs in Langfuse
    }
    if handler is not None:
        cfg["callbacks"] = [handler]
    return cfg


def log_human_decision(handler, action: str) -> None:
    """Attach the reviewer's decision to the trace as a categorical score."""
    if handler is None:
        return
    try:
        from langfuse import get_client
        trace_id = getattr(handler, "last_trace_id", None)
        if trace_id:
            get_client().create_score(
                trace_id=trace_id, name="human_decision",
                value=action, data_type="CATEGORICAL",
            )
    except Exception:
        pass
