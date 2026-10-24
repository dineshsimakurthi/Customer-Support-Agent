"""Create tables and insert fake orders. Run: python scripts/seed_db.py"""
import random
import sys
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import db  # noqa: E402

FIXED = [  # used by the sample tickets, so keep these stable
    ("ORD-1001", "Alice Johnson", "Pro Laptop 15", 1299.00, "delivered", 10),
    ("ORD-1002", "Ben Carter", "Wireless Headphones", 89.00, "shipped", 3),
    ("ORD-1003", "Chitra Rao", "Smartphone X", 649.00, "delivered", 12),
    ("ORD-1004", "Dan Lee", "USB-C Cable 2m", 19.00, "processing", 0),
    ("ORD-1005", "Eva Moreno", "Smartwatch S2", 199.00, "delivered", 20),
]
PRODUCTS = [("Bluetooth Speaker", 59), ("Gaming Mouse", 45), ("4K Monitor", 329),
            ("Mechanical Keyboard", 119), ("Tablet Pro 11", 799), ("Webcam HD", 69)]
NAMES = ["Farid Khan", "Grace Kim", "Hiro Tanaka", "Isla Brown", "Jon Smith", "Kavya Nair"]
STATUSES = ["processing", "shipped", "delivered", "delivered", "returned"]


def main():
    random.seed(42)
    db.init_db()
    today = date.today()
    rows = [(oid, c, p, a, s, str(today - timedelta(days=d))) for oid, c, p, a, s, d in FIXED]
    for i in range(6, 31):
        product, price = random.choice(PRODUCTS)
        rows.append((f"ORD-{1000 + i}", random.choice(NAMES), product, float(price),
                     random.choice(STATUSES), str(today - timedelta(days=random.randint(0, 40)))))
    with closing(db.get_conn()) as conn:
        conn.executemany("INSERT OR REPLACE INTO orders VALUES (?,?,?,?,?,?)", rows)
        conn.commit()
    print(f"Seeded {len(rows)} orders into {db.config.DB_PATH}")


if __name__ == "__main__":
    main()
