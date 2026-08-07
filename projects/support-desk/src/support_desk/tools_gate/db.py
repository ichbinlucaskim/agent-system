"""SQLite account state for orders, refunds, and escalation tickets.

Purpose
    Provide a small, always-fresh account database: connect, seed from SQL,
    read orders/refunds, and apply refund / cancel / ticket writes.

Why
    Case 06 requires tools to re-read live state rather than trust conversation
    memory. A real SQLite file (even a temp one) makes stale-state bugs and
    post-action status checks observable in eval.

Trade-offs
    ``init_db`` deletes any existing file at the path—convenient for demos and
    tests, unsafe if pointed at a shared production DB by mistake. Mutations
    commit immediately; there is no multi-step transaction API.

Edges
    Unknown ``order_id`` raises ``KeyError`` on write helpers. Callers in the
    tool layer convert that into tool-result error strings. Never cache rows
    across turns; always call ``get_order`` again before acting.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from support_desk.paths import SEED_SQL


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection with row factory and foreign keys.

    Purpose
        Return a connection ready for dict-like row access and FK enforcement.

    Why
        Shared setup so every caller gets the same pragmas and does not forget
        ``row_factory``.

    Trade-offs
        Does not create or seed tables—call ``init_db`` for a fresh store, or
        point at an already-seeded file.

    Edges
        Path is coerced to ``str`` for ``sqlite3.connect``. Missing parents are
        not created here (unlike ``init_db``).
    """
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: str | Path, *, seed_sql: Path | None = None) -> sqlite3.Connection:
    """Create a fresh database from seed.sql.

    Purpose
        Wipe any file at ``db_path``, apply the seed script, and return an open
        connection.

    Why
        Eval and smoke paths need identical starting orders every run. Seeding
        from a checked-in SQL file keeps fixtures reproducible.

    Trade-offs
        Destructive by design: existing DB files are unlinked. Suitable for
        lab temp files, not for long-lived customer data without a backup path.

    Edges
        Parent directories are created if missing. ``seed_sql`` defaults to
        ``SEED_SQL`` from ``paths``.
    """
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
    """Load one order row as a plain dict, or None if missing.

    Purpose
        Fetch current order fields for lookup tools and write preconditions.

    Why
        Tools and the policy gate must see live status / totals / delivery age
        before confirming side effects.

    Trade-offs
        Returns a shallow ``dict`` copy of the row, not a typed model—callers
        use string keys matching the seed schema.

    Edges
        Missing order → ``None`` (not an exception). Write helpers raise
        ``KeyError`` instead when they require the row to exist.
    """
    row = connection.execute(
        "SELECT * FROM orders WHERE order_id = ?", (order_id,)
    ).fetchone()
    return dict(row) if row else None


def list_refunds(connection: sqlite3.Connection, order_id: str) -> list[dict]:
    """List refund rows for an order, ordered by refund id.

    Purpose
        Support eval assertions on refund amount after ``issue_refund``.

    Why
        Action-level eval checks DB outcomes, not only model text.

    Trade-offs
        No pagination; fine for the tiny seed corpus.

    Edges
        Unknown order yields an empty list, not an error.
    """
    rows = connection.execute(
        "SELECT * FROM refunds WHERE order_id = ? ORDER BY refund_id",
        (order_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def issue_refund(
    connection: sqlite3.Connection, order_id: str, amount_usd: float
) -> dict:
    """Apply a refund after callers have already enforced policy.

    Purpose
        Insert a refund row, mark the order ``refunded``, and return a summary
        payload.

    Why
        Separates persistence from policy: tool preconditions and HITL run
        first; this function only mutates when those gates have passed.

    Trade-offs
        No re-check of window / amount / status here—duplicate enforcement would
        hide bugs in the tool layer. Callers must not skip the gate.

    Edges
        Unknown ``order_id`` raises ``KeyError``. Commits immediately.
    """
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
    """Mark an order cancelled in the database.

    Purpose
        Persist cancellation after tool-layer status checks have passed.

    Why
        Same split as refunds: DB writes are dumb; policy lives above.

    Trade-offs
        Does not verify ``processing`` status—``cancel_order_tool`` must.

    Edges
        Unknown ``order_id`` raises ``KeyError``.
    """
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
    """Insert an escalation ticket and return its id and fields.

    Purpose
        Record human-handoff cases without moving money or order status.

    Why
        Escalation is an auto-approved side effect that still needs an audit
        trail in the DB for eval and demos.

    Trade-offs
        ``order_id`` is optional; no FK validation beyond SQLite pragmas on the
        seed schema.

    Edges
        Returns ``ticket_id`` from ``lastrowid``. Commits immediately.
    """
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
