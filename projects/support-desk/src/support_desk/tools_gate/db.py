"""SQLite account state. Always read fresh; never cache in the conversation."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from support_desk.paths import SEED_SQL


def connect(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: str | Path, *, seed_sql: Path | None = None) -> sqlite3.Connection:
    """Create a fresh database from seed.sql."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    sql = (seed_sql or SEED_SQL).read_text(encoding="utf-8")
    connection = connect(path)
    connection.executescript(sql)
    connection.commit()
    return connection


def get_order(connection: sqlite3.Connection, order_id: str) -> dict | None:
    row = connection.execute(
        "SELECT * FROM orders WHERE order_id = ?", (order_id,)
    ).fetchone()
    return dict(row) if row else None


def list_refunds(connection: sqlite3.Connection, order_id: str) -> list[dict]:
    rows = connection.execute(
        "SELECT * FROM refunds WHERE order_id = ? ORDER BY refund_id",
        (order_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def issue_refund(
    connection: sqlite3.Connection, order_id: str, amount_usd: float
) -> dict:
    """Apply a refund after callers have already enforced policy."""
    order = get_order(connection, order_id)
    if order is None:
        raise KeyError(f"unknown order {order_id!r}")
    connection.execute(
        "INSERT INTO refunds (order_id, amount_usd) VALUES (?, ?)",
        (order_id, amount_usd),
    )
    connection.execute(
        "UPDATE orders SET status = ? WHERE order_id = ?",
        ("refunded", order_id),
    )
    connection.commit()
    return {
        "order_id": order_id,
        "amount_usd": amount_usd,
        "status": "refunded",
    }


def cancel_order(connection: sqlite3.Connection, order_id: str) -> dict:
    order = get_order(connection, order_id)
    if order is None:
        raise KeyError(f"unknown order {order_id!r}")
    connection.execute(
        "UPDATE orders SET status = ? WHERE order_id = ?",
        ("cancelled", order_id),
    )
    connection.commit()
    return {"order_id": order_id, "status": "cancelled"}


def add_ticket(
    connection: sqlite3.Connection,
    *,
    customer_id: str,
    reason: str,
    order_id: str | None = None,
) -> dict:
    cursor = connection.execute(
        "INSERT INTO tickets (customer_id, order_id, reason) VALUES (?, ?, ?)",
        (customer_id, order_id, reason),
    )
    connection.commit()
    return {
        "ticket_id": cursor.lastrowid,
        "customer_id": customer_id,
        "order_id": order_id,
        "reason": reason,
    }
