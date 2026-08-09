"""SQLite 시드 DB와 조회 헬퍼.

Purpose
    연습용 고객·계좌·이체·감사 로그를 로컬 SQLite에 둔다.

Why
    코어뱅킹 HTTP 없이 사전조건·감사 스토리를 재현 가능하게 한다.

Trade-offs
    인메모리 DB는 테스트에 편하지만 프로세스 밖 공유는 없다.

Edges
    seed.sql 경로가 없으면 즉시 실패한다.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from regulated_transfer.packaging.config import SEED_SQL


def connect(db_path: str | Path = ":memory:") -> sqlite3.Connection:
    """시드가 적용된 연결을 연다."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SEED_SQL.read_text(encoding="utf-8"))
    return conn


def get_account(conn: sqlite3.Connection, account_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM accounts WHERE account_id = ?",
        (account_id,),
    ).fetchone()


def get_customer(conn: sqlite3.Connection, customer_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM customers WHERE customer_id = ?",
        (customer_id,),
    ).fetchone()


def list_accounts_for_customer(conn: sqlite3.Connection, customer_id: str) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT * FROM accounts WHERE customer_id = ?",
            (customer_id,),
        )
    )
