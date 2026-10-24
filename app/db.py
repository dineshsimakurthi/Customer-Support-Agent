"""SQLite helpers: orders table (seeded) and ticket_log table (written by the agent)."""
import sqlite3
from contextlib import closing

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    order_id   TEXT PRIMARY KEY,
    customer   TEXT,
    product    TEXT,
    amount     REAL,
    status     TEXT,
    order_date TEXT
);
CREATE TABLE IF NOT EXISTS ticket_log (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id      TEXT,
    ticket         TEXT,
    category       TEXT,
    urgency        TEXT,
    sentiment      TEXT,
    confidence     REAL,
    route          TEXT,
    status         TEXT,
    human_decision TEXT,
    final_reply    TEXT,
    reasons        TEXT,
    created_at     TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def get_conn() -> sqlite3.Connection:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_conn()) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def get_order(order_id: str) -> dict | None:
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
    return dict(row) if row else None
