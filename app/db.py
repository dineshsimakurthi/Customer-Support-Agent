"""SQLite helpers: orders table (seeded) and ticket_log table (written by the agent)."""
import sqlite3
from contextlib import closing

from app import config

SAMPLE_ORDERS = [
    ("ORD-1001", "Alice Johnson", "Pro Laptop 15", 1299.00, "delivered", "2026-01-05"),
    ("ORD-1002", "Ben Carter", "Wireless Headphones", 89.00, "shipped", "2026-01-12"),
    ("ORD-1003", "Chitra Rao", "Smartphone X", 649.00, "delivered", "2026-01-19"),
    ("ORD-1004", "Dan Lee", "USB-C Cable 2m", 19.00, "processing", "2026-01-25"),
    ("ORD-1005", "Eva Moreno", "Smartwatch S2", 199.00, "delivered", "2026-02-01"),
]

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
        if conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
            conn.executemany(
                "INSERT OR IGNORE INTO orders (order_id, customer, product, amount, status, order_date) VALUES (?, ?, ?, ?, ?, ?)",
                SAMPLE_ORDERS,
            )
        conn.commit()


def get_order(order_id: str) -> dict | None:
    normalized = (order_id or "").strip().upper()
    if not normalized:
        return None
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT * FROM orders WHERE order_id = ?", (normalized,)).fetchone()
    return dict(row) if row else None
