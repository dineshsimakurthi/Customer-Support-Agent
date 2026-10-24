"""Node 5b: pause the graph until a human approves, edits or rejects the draft."""
from langgraph.types import interrupt

STATUS = {"approve": "approved", "edit": "edited", "reject": "rejected"}


def human_review_node(state):
    # The graph stops here and returns this payload to the caller (the UI).
    # It resumes when the UI calls graph.invoke(Command(resume={...}), config).
    decision = interrupt({
        "ticket": state["ticket"],
        "category": state.get("category"),
        "draft": state["draft"],
        "reasons": state.get("reasons", []),
    })
    action = decision.get("action", "reject")
    if action == "approve":
        reply = state["draft"]
    elif action == "edit":
        reply = decision.get("reply") or state["draft"]
    else:
        action, reply = "reject", ""
    return {
        "human_decision": action,
        "final_reply": reply,
        "route": "human",
        "status": STATUS[action],
    }
