"""Streamlit demo. Run: streamlit run ui/streamlit_app.py"""
import html
import json
import sys
import uuid
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from langgraph.types import Command  # noqa: E402

from app import config, db  # noqa: E402
from app.graph import get_graph  # noqa: E402
from app.observability import get_handler, log_human_decision, make_run_config  # noqa: E402

st.set_page_config(page_title="Support Triage Agent", page_icon="🎧", layout="wide")

# ====================================================================== styling
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root {
  --bg:#0b0f14;
  --bg-2:#121821;
  --panel:#121b23;
  --panel-2:#0e141b;
  --line:rgba(188,197,210,.12);
  --text:#edf2f7;
  --muted:#9aa7b7;
  --soft:#dfe7f2;
  --accent:#a8b1c1;
  --accent-strong:#c6cfdd;
  --accent-soft:rgba(168,177,193,.10);
  --success:#a7b8ae;
  --warn:#b9af92;
  --danger:#b88b8e;
  --shadow:rgba(2,5,10,.38);
}
html, body, [class*="st-"] { font-family:'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif; }
#MainMenu, footer { visibility:hidden; }
header[data-testid="stHeader"] { background:transparent; }
.stApp {
  background: linear-gradient(180deg, #0b0f14 0%, #111821 100%);
}
.block-container { padding-top:1.5rem; max-width:1240px; }
[data-testid="stSidebar"] {
  background: rgba(11, 15, 20, 0.96);
  backdrop-filter: blur(12px);
  border-right: 1px solid var(--line);
}

.glass {
  background: rgba(18, 24, 31, 0.8);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 1.1rem 1.3rem;
  margin-bottom: 1rem;
  box-shadow: 0 10px 28px var(--shadow);
}
.hero {
  padding: 1.6rem 1.8rem;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(168,177,193,.04), rgba(255,255,255,.02));
}
.hero::before {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at top left, rgba(168,177,193,.06), transparent 42%);
  pointer-events: none;
}
.hero h1 {
  margin: 0;
  font-size: 2.1rem;
  font-weight: 700;
  letter-spacing: -0.04em;
  color: var(--text);
}
.hero p { margin: .45rem 0 .9rem; color: var(--muted); font-size: .98rem; }
.chip {
  display: inline-block;
  padding: .32rem .8rem;
  border-radius: 999px;
  font-size: .76rem;
  font-weight: 600;
  background: rgba(255,255,255,.04);
  border: 1px solid var(--line);
  color: var(--soft);
  margin: 0 .45rem .45rem 0;
}
.lbl {
  font-size: .68rem;
  text-transform: uppercase;
  letter-spacing: .12em;
  color: var(--muted);
  font-weight: 700;
  margin-bottom: .5rem;
}

.badge { display:inline-block; padding:.28rem .78rem; border-radius:999px; font-size:.77rem; font-weight:700; }
.b-violet { color:#dce3ee; background:rgba(168,177,193,.08); border:1px solid rgba(168,177,193,.22); }
.b-green  { color:#d6e0d9; background:rgba(167,184,174,.08); border:1px solid rgba(167,184,174,.22); }
.b-blue   { color:#dfe7f5; background:rgba(150,163,182,.08); border:1px solid rgba(150,163,182,.22); }
.b-amber  { color:#e8e0d0; background:rgba(185,175,146,.08); border:1px solid rgba(185,175,146,.22); }
.b-red    { color:#e6d0d1; background:rgba(184,139,142,.08); border:1px solid rgba(184,139,142,.22); }
.b-gray   { color:#dfe7f7; background:rgba(148,163,184,.08); border:1px solid rgba(148,163,184,.22); }

.stepper { display:flex; align-items:flex-start; width:100%; }
.stg { display:flex; flex-direction:column; align-items:center; gap:.45rem; min-width:78px; }
.dot { width:42px; height:42px; border-radius:50%; display:grid; place-items:center; font-size:1.1rem; border:1px solid var(--line); background:rgba(255,255,255,.03); }
.stg-l { font-size:.7rem; font-weight:600; color:var(--muted); text-align:center; }
.stg-done .dot { background:rgba(168,177,193,.08); border-color: rgba(168,177,193,.18); }
.stg-done .stg-l { color: var(--soft); }
.stg-wait .dot { background: rgba(185,175,146,.08); border-color: rgba(185,175,146,.18); }
.stg-wait .stg-l { color: var(--warn); }
.link { flex:1; height:2px; margin-top:20px; background:rgba(255,255,255,.08); border-radius:2px; }
.link-on { background:linear-gradient(90deg, rgba(168,177,193,.6), rgba(198,207,221,.5)); }

.msg { display:flex; gap:.8rem; margin:.55rem 0 1rem; align-items:flex-start; }
.msg-agent { flex-direction:row-reverse; }
.avatar { width:38px; height:38px; border-radius:50%; display:grid; place-items:center; font-size:1.1rem; flex:none; }
.av-customer { background: rgba(255,255,255,.05); border:1px solid var(--line); }
.av-agent { background: rgba(168,177,193,.08); border:1px solid rgba(168,177,193,.16); }
.bub {
  max-width:84%; padding: .85rem 1rem; border-radius: 16px; line-height: 1.6; font-size: .94rem;
  border: 1px solid var(--line);
}
.bub-customer { background: rgba(255,255,255,.03); border-top-left-radius: 6px; }
.bub-agent { background: rgba(168,177,193,.04); border-top-right-radius: 6px; border-color: rgba(168,177,193,.12); }
.who { font-size:.7rem; text-transform:uppercase; letter-spacing:.11em; color:var(--muted); font-weight:700; margin-bottom:.25rem; }
.txt { white-space:pre-wrap; }

.alert { border-radius: 14px; padding: .9rem 1rem; margin: .4rem 0 1rem; border: 1px solid; }
.alert ul { margin: .45rem 0 0 1.1rem; padding:0; }
.alert-warn { background: rgba(185,175,146,.08); border-color: rgba(185,175,146,.2); }
.alert-ok { background: rgba(167,184,174,.08); border-color: rgba(167,184,174,.2); }
.alert-info { background: rgba(168,177,193,.08); border-color: rgba(168,177,193,.2); }

.kv { display:flex; justify-content:space-between; padding:.42rem 0; border-bottom:1px dashed var(--line); }
.kv:last-child { border-bottom:none; }
.kv span:first-child { color:var(--muted); }

.kpi-v { font-size:2.1rem; font-weight:700; letter-spacing:-.03em; color:var(--soft); }

[data-testid="stTextArea"] textarea {
  background: rgba(255,255,255,.03) !important;
  border: 1px solid rgba(255,255,255,.12) !important;
  border-radius: 12px !important;
  color: var(--text) !important;
}
[data-testid="stTextArea"] textarea:focus {
  border-color: rgba(168,177,193,.28) !important;
  box-shadow: 0 0 0 3px rgba(168,177,193,.08) !important;
}
[data-baseweb="select"] > div {
  background: rgba(255,255,255,.03) !important;
  border: 1px solid rgba(255,255,255,.12) !important;
  border-radius: 12px !important;
}
div.stButton > button {
  border-radius: 12px;
  font-weight: 600;
  padding: .6rem 1.1rem;
  border: 1px solid rgba(255,255,255,.12);
  background: rgba(255,255,255,.04);
  color: var(--text);
}
div.stButton > button:hover {
  border-color: rgba(168,177,193,.22);
  background: rgba(168,177,193,.07);
}
button[data-testid="stBaseButton-primary"], div.stButton > button[kind="primary"] {
  background: rgba(168,177,193,.08);
  border: 1px solid rgba(168,177,193,.22);
  color: var(--text);
  box-shadow: none;
}
[data-testid="stExpander"] {
  border: 1px solid var(--line) !important;
  background: rgba(255,255,255,.02);
  border-radius: 14px !important;
}
.stTabs [data-baseweb="tab-list"] {
  gap: .35rem;
  background: rgba(255,255,255,.02);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: .2rem;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 10px;
  padding: .45rem 1.1rem;
  color: var(--muted);
  font-weight: 600;
}
.stTabs [aria-selected="true"] {
  background: rgba(168,177,193,.08);
  color: var(--text);
}
</style>
""",
    unsafe_allow_html=True,
)

# ====================================================================== helpers
URGENCY_COLOR = {"low": "green", "medium": "blue", "high": "amber", "critical": "red"}
SENTIMENT_COLOR = {"positive": "green", "neutral": "gray", "negative": "amber", "angry": "red"}
STAGES = [
    ("classify", "Classify", "🧭"), ("lookup_order", "Order lookup", "📦"),
    ("retrieve", "Retrieve", "📚"), ("draft", "Draft", "✍️"),
    ("confidence", "Confidence", "🛡️"), ("decision", "Decision", "⚖️"), ("log", "Log", "🗂️"),
]


def esc(value) -> str:
    """HTML-escape, and neutralise '$' so Streamlit does not treat it as LaTeX math."""
    return html.escape(str(value)).replace("$", "&#36;")


def badge(text, kind="gray") -> str:
    return f'<span class="badge b-{kind}">{esc(text)}</span>'


def stage_status(key, trace, waiting):
    if key == "decision":
        if "auto_send" in trace or "human_review" in trace:
            return "done"
        return "wait" if waiting else "idle"
    if key in trace:
        return "done"
    if key == "lookup_order" and "retrieve" in trace:
        return "skip"
    return "idle"


def stepper_html(trace, waiting) -> str:
    parts, prev_done = [], None
    for key, label, icon in STAGES:
        status = stage_status(key, trace, waiting)
        if key == "decision":
            label = "Auto-send" if "auto_send" in trace else "Human review" if (
                "human_review" in trace or waiting) else "Decision"
        if prev_done is not None:
            parts.append(f'<div class="link {"link-on" if status in ("done", "wait") and prev_done else ""}"></div>')
        parts.append(f'<div class="stg stg-{status}"><div class="dot">{icon}</div><div class="stg-l">{esc(label)}</div></div>')
        prev_done = status in ("done", "skip")
    return '<div class="stepper">' + "".join(parts) + "</div>"


def ring_html(conf) -> str:
    if conf is None:
        return (
            '<div class="ring-wrap"><div class="ring" style="background:conic-gradient(#fbbf24 100%, #fbbf24 0)">'
            '<div class="ring-in">🛡️</div></div><div class="ring-note"><b style="color:#fcd34d">Rule-based escalation</b><br>'
            "A safety rule fired, so the model's self-rating was skipped.</div></div>"
        )
    pct = max(0, min(100, round(conf * 100)))
    ok = conf >= config.CONFIDENCE_THRESHOLD
    colours = "#22d3ee, #8b5cf6" if ok else "#fbbf24, #fb7185"
    verdict = "Above threshold, safe to auto-send." if ok else "Below threshold, needs a human."
    return (
        f'<div class="ring-wrap"><div class="ring" style="background:conic-gradient(from 0deg, {colours} {pct}%, rgba(255,255,255,.08) {pct}%)">'
        f'<div class="ring-in">{conf:.2f}</div></div><div class="ring-note"><b>Model confidence</b><br>{verdict}<br>'
        f"Threshold {config.CONFIDENCE_THRESHOLD}</div></div>"
    )


def bars_html(series) -> str:
    top = max(series.max(), 1)
    rows = "".join(
        f'<div class="row"><div class="name">{esc(k)}</div><div class="track"><div class="fill" '
        f'style="width:{v / top * 100:.0f}%"></div></div><div class="num">{v}</div></div>'
        for k, v in series.items()
    )
    return f'<div class="bars">{rows}</div>'


def bubble(role, who, text) -> str:
    avatar = "👤" if role == "customer" else "🤖"
    return (
        f'<div class="msg msg-{role}"><div class="avatar av-{role}">{avatar}</div>'
        f'<div class="bub bub-{role}"><div class="who">{esc(who)}</div><div class="txt">{esc(text)}</div></div></div>'
    )


@st.cache_resource
def load_graph():
    db.init_db()
    return get_graph()


@st.cache_data
def load_samples():
    path = config.TESTS_DIR / "test_set.json"
    return [c["ticket"] for c in json.loads(path.read_text())] if path.exists() else []


def run(inputs, thread_id):
    """Stream the graph, collect executed node names, return the Langfuse handler."""
    graph, handler = load_graph(), get_handler()
    cfg = make_run_config(thread_id, handler)
    for chunk in graph.stream(inputs, cfg, stream_mode="updates"):
        for node in chunk:
            if node != "__interrupt__":
                st.session_state.trace.append(node)
    return handler


def current_state():
    cfg = {"configurable": {"thread_id": st.session_state.thread_id}}
    snap = load_graph().get_state(cfg)
    return snap.values, bool(snap.next)


def load_sample():
    if st.session_state.get("sample_choice"):
        st.session_state.ticket_text = st.session_state.sample_choice


for key, default in [("thread_id", None), ("trace", []), ("ticket_text", "")]:
    st.session_state.setdefault(key, default)

# ====================================================================== sidebar
with st.sidebar:
    st.markdown(
        '<div style="font-size:1.35rem;font-weight:800;margin-bottom:.8rem">🎧 Triage<span style="color:#22d3ee">AI</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="lbl">Try a sample ticket</div>', unsafe_allow_html=True)
    st.selectbox("Sample", [""] + load_samples(), key="sample_choice", on_change=load_sample,
                 label_visibility="collapsed")
    st.markdown(
        '<div class="glass" style="padding:1rem 1.1rem"><div class="lbl">Configuration</div>'
        f'<div class="kv"><span>Provider</span><span>{esc(config.LLM_PROVIDER)}</span></div>'
        f'<div class="kv"><span>Failover</span><span>{esc(", ".join(config.LLM_FALLBACKS) or "none")}</span></div>'
        f'<div class="kv"><span>Confidence ≥</span><span>{config.CONFIDENCE_THRESHOLD}</span></div>'
        f'<div class="kv"><span>Refund limit</span><span>&#36;{config.REFUND_LIMIT:,.0f}</span></div>'
        f'<div class="kv"><span>Langfuse</span><span>{"● on" if config.LANGFUSE_ENABLED else "○ off"}</span></div></div>'
        '<div class="glass" style="padding:1rem 1.1rem"><div class="lbl">Escalates to a human when</div>'
        '<div style="font-size:.88rem;line-height:1.9;color:#cbd5e1">😡 customer is angry<br>🚨 urgency is critical<br>'
        "💸 refund is over the limit<br>🔍 order not found<br>📭 no knowledge found<br>📉 confidence is low</div></div>",
        unsafe_allow_html=True,
    )

# ====================================================================== hero
st.markdown(
    '<div class="glass hero"><h1>Customer Support Triage Agent</h1>'
    "<p>Reads the ticket, checks the order, finds the policy, writes the reply, "
    "and hands anything risky to a human before it is sent.</p>"
    f'<span class="chip">🧠 {esc(config.LLM_PROVIDER)} · {esc(config.LLM_MODEL)}</span>'
    '<span class="chip">🕸️ LangGraph</span><span class="chip">📚 Chroma RAG</span>'
    '<span class="chip">🙋 Human-in-the-loop</span><span class="chip">🔭 Langfuse</span></div>',
    unsafe_allow_html=True,
)

tab_triage, tab_metrics = st.tabs(["🎫  Triage", "📊  Metrics"])

# ====================================================================== triage tab
with tab_triage:
    st.markdown('<div class="lbl" style="margin-top:.6rem">Incoming ticket</div>', unsafe_allow_html=True)
    ticket = st.text_area(
        "Customer ticket", key="ticket_text", height=110, label_visibility="collapsed",
        placeholder="Paste a customer message here, or pick a sample from the sidebar…",
    )
    go = st.button("✨  Process ticket", type="primary", disabled=not ticket.strip())

    if go:
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.trace = []
        with st.spinner("Agent is working…"):
            try:
                run({"ticket": ticket.strip()}, st.session_state.thread_id)
            except Exception as exc:
                st.error(f"Run failed: {exc}")

    state, awaiting = ({}, False)
    if st.session_state.thread_id:
        state, awaiting = current_state()

    if not state.get("category"):
        st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
        for col, icon, title, text in zip(
            st.columns(3),
            ["🧭", "📚", "🛡️"],
            ["1 · Understand", "2 · Ground the answer", "3 · Protect the customer"],
            ["Classifies every ticket by category, urgency and sentiment.",
             "Looks up the order and retrieves policy and FAQ answers so replies are never invented.",
             "Auto-sends safe replies and pauses risky ones for a human to approve, edit or reject."],
        ):
            col.markdown(
                f'<div class="glass feat"><div class="ic">{icon}</div><b>{title}</b><div class="d">{text}</div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            f'<div class="glass"><div class="lbl">Agent pipeline</div>{stepper_html(st.session_state.trace, awaiting)}</div>',
            unsafe_allow_html=True,
        )
        left, right = st.columns([7, 5], gap="large")

        # ---------------- left: conversation + decision
        with left:
            final = state.get("final_reply")
            reply_text = final if final else state.get("draft", "")
            who = "ShopEasy Support · final reply" if final else "ShopEasy Support · draft"
            if state.get("status") == "rejected":
                reply_text, who = "(reply rejected by the reviewer, nothing was sent)", "ShopEasy Support"
            st.markdown(
                '<div class="glass"><div class="lbl">Conversation</div>'
                + bubble("customer", "Customer", state.get("ticket", ticket))
                + bubble("agent", who, reply_text)
                + "</div>",
                unsafe_allow_html=True,
            )

            if awaiting:
                reasons = "".join(f"<li>{esc(r)}</li>" for r in state.get("reasons", []))
                st.markdown(
                    '<div class="alert alert-warn"><b>⏸️ Waiting for a human decision</b>'
                    f"<ul>{reasons}</ul></div>",
                    unsafe_allow_html=True,
                )
                edited = st.text_area(
                    "Edit the reply before sending", value=state.get("draft", ""), height=170,
                    key=f"edit_{st.session_state.thread_id}",
                )
                b1, b2, b3 = st.columns(3)
                decision = None
                if b1.button("✅  Approve", type="primary"):
                    decision = {"action": "approve"}
                if b2.button("✏️  Send edited"):
                    decision = {"action": "edit", "reply": edited}
                if b3.button("❌  Reject"):
                    decision = {"action": "reject"}
                if decision:
                    handler = run(Command(resume=decision), st.session_state.thread_id)
                    log_human_decision(handler, decision["action"])
                    st.rerun()
            elif state.get("status") == "auto_sent":
                st.markdown(
                    '<div class="alert alert-ok"><b>✅ Auto-sent</b> · high confidence and no risk rules triggered</div>',
                    unsafe_allow_html=True,
                )
            elif state.get("status"):
                st.markdown(
                    f'<div class="alert alert-info"><b>👤 Human decision:</b> {esc(state["status"])}</div>',
                    unsafe_allow_html=True,
                )

        # ---------------- right: insights
        with right:
            urgency, sentiment = state["urgency"], state["sentiment"]
            st.markdown(
                '<div class="glass"><div class="lbl">Classification</div><div class="trio">'
                f'<div><div class="lbl">Category</div>{badge(state["category"], "violet")}</div>'
                f'<div><div class="lbl">Urgency</div>{badge(urgency, URGENCY_COLOR.get(urgency, "gray"))}</div>'
                f'<div><div class="lbl">Sentiment</div>{badge(sentiment, SENTIMENT_COLOR.get(sentiment, "gray"))}</div>'
                "</div></div>"
                f'<div class="glass">{ring_html(state.get("confidence"))}</div>',
                unsafe_allow_html=True,
            )
            order = state.get("order_info")
            if order:
                st.markdown(
                    '<div class="glass"><div class="lbl">Order details</div>'
                    f'<div class="kv"><span>Order</span><span>{esc(order["order_id"])}</span></div>'
                    f'<div class="kv"><span>Product</span><span>{esc(order["product"])}</span></div>'
                    f'<div class="kv"><span>Amount</span><span>{esc("${:,.2f}".format(order["amount"]))}</span></div>'
                    f'<div class="kv"><span>Status</span><span>{esc(order["status"])}</span></div>'
                    f'<div class="kv"><span>Date</span><span>{esc(order["order_date"])}</span></div></div>',
                    unsafe_allow_html=True,
                )
            docs = state.get("docs", [])
            with st.expander(f"📎 Retrieved sources ({len(docs)})"):
                if not docs:
                    st.caption("Nothing retrieved. Run scripts/ingest_kb.py to build the knowledge base.")
                for d in docs:
                    st.markdown(f"**{d['source']}** · {d.get('type', '')} · score {d.get('score', '–')}")
                    st.caption(d["content"][:300])

# ====================================================================== metrics tab
with tab_metrics:
    db.init_db()
    with closing(db.get_conn()) as conn:
        df = pd.read_sql_query("SELECT * FROM ticket_log ORDER BY id DESC", conn)
    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    if df.empty:
        st.markdown(
            '<div class="glass" style="text-align:center;padding:2.5rem"><div style="font-size:2.4rem">📭</div>'
            "<b>No tickets processed yet</b><div style='color:var(--muted)'>Process one in the Triage tab and "
            "your stats will appear here.</div></div>",
            unsafe_allow_html=True,
        )
    else:
        total = len(df)
        auto = int((df["route"] == "auto").sum())
        avg_conf = df["confidence"].dropna().mean()
        kpis = [
            ("🎫", "Tickets processed", f"{total}"),
            ("⚡", "Auto-resolved", f"{auto / total:.0%}"),
            ("🙋", "Escalated to human", f"{(total - auto) / total:.0%}"),
            ("🎯", "Avg confidence", f"{avg_conf:.2f}" if pd.notna(avg_conf) else "–"),
        ]
        for col, (icon, label, value) in zip(st.columns(4), kpis):
            col.markdown(
                f'<div class="glass"><div style="font-size:1.4rem">{icon}</div><div class="kpi-v">{value}</div>'
                f'<div class="lbl" style="margin:0">{label}</div></div>',
                unsafe_allow_html=True,
            )
        c1, c2 = st.columns(2, gap="large")
        c1.markdown(
            f'<div class="glass"><div class="lbl">Tickets by category</div>{bars_html(df["category"].value_counts())}</div>',
            unsafe_allow_html=True,
        )
        c2.markdown(
            f'<div class="glass"><div class="lbl">Outcomes</div>{bars_html(df["status"].value_counts())}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="lbl">Recent tickets</div>', unsafe_allow_html=True)
        st.dataframe(
            df[["created_at", "category", "urgency", "sentiment", "confidence", "route", "status", "reasons"]],
            hide_index=True,
        )