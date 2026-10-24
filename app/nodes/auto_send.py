"""Node 5a: low-risk, high-confidence tickets are answered automatically."""


def auto_send_node(state):
    return {
        "final_reply": state["draft"],
        "route": "auto",
        "status": "auto_sent",
        "human_decision": None,
    }
