"""도구 스키마·실행기 — 사전조건이 권한의 본체.

Purpose
    정책검색·잔액조회·이체·에스컬레이션·금지 tool을 정의하고 실행한다.

Why
    모델이 “승인된 척”해도 한도·잔액·본인확인은 여기서 다시 검사한다.

Trade-offs
    코어뱅킹 API 대신 SQLite. 금액은 원 단위 정수.

Edges
    미확인 세션·한도 초과·잔액 부족은 Error: 접두로 돌려 executed=False가 된다.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from regulated_transfer.packaging.config import DAILY_LIMIT_KRW, ONCE_LIMIT_KRW, POLICY_DIR
from regulated_transfer.tools_gate import db
from regulated_transfer.tools_gate.pii import mask_account_id, mask_pii
from regulated_transfer.tools_gate.session import SessionContext

ToolFn = Callable[[dict[str, Any], SessionContext], str]


def _search_policy(arguments: dict[str, Any], ctx: SessionContext) -> str:
    query = str(arguments.get("query", "")).strip().lower()
    chunks: list[str] = []
    for path in sorted(POLICY_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not query or query in text.lower() or any(tok in text.lower() for tok in query.split()):
            chunks.append(f"## {path.name}\n{text.strip()}")
    if not chunks:
        return "관련 정책 문서를 찾지 못했습니다."
    return mask_pii("\n\n".join(chunks)[:4000])


def _lookup_balance(arguments: dict[str, Any], ctx: SessionContext) -> str:
    if not ctx.verified:
        return "Error: 본인확인되지 않은 세션에서는 잔액을 조회할 수 없습니다."
    account_id = str(arguments.get("account_id", "")).strip()
    row = db.get_account(ctx.connection, account_id)
    if row is None:
        return "Error: 계좌를 찾을 수 없습니다."
    if row["customer_id"] != ctx.customer_id:
        return "Error: 본인 명의 계좌만 조회할 수 있습니다."
    cust = db.get_customer(ctx.connection, ctx.customer_id)
    payload = {
        "account_id": mask_account_id(account_id),
        "customer_name": cust["name"] if cust else "",
        "balance_krw": row["balance"],
        "daily_transferred_krw": row["daily_transferred"],
        "once_limit_krw": ONCE_LIMIT_KRW,
        "daily_limit_krw": DAILY_LIMIT_KRW,
    }
    return mask_pii(json.dumps(payload, ensure_ascii=False))


def _transfer(arguments: dict[str, Any], ctx: SessionContext) -> str:
    if not ctx.verified:
        return "Error: 본인확인되지 않은 세션에서는 이체할 수 없습니다."
    from_account = str(arguments.get("from_account", "")).strip()
    to_account = str(arguments.get("to_account", "")).strip()
    try:
        amount = int(arguments.get("amount_krw"))
    except (TypeError, ValueError):
        return "Error: amount_krw는 정수(원)여야 합니다."

    if amount <= 0:
        return "Error: 이체 금액은 1원 이상이어야 합니다."
    if amount > ONCE_LIMIT_KRW:
        return (
            f"Error: 1회 이체 한도({ONCE_LIMIT_KRW:,}원)를 초과했습니다. "
            "상담원 에스컬레이션이 필요합니다."
        )

    src = db.get_account(ctx.connection, from_account)
    if src is None:
        return "Error: 출금 계좌를 찾을 수 없습니다."
    if src["customer_id"] != ctx.customer_id:
        return "Error: 본인 명의 계좌에서만 출금할 수 있습니다."
    if db.get_account(ctx.connection, to_account) is None:
        return "Error: 입금 계좌를 찾을 수 없습니다."

    if src["daily_transferred"] + amount > DAILY_LIMIT_KRW:
        return (
            f"Error: 1일 이체 한도({DAILY_LIMIT_KRW:,}원)를 초과합니다. "
            "상담원 에스컬레이션이 필요합니다."
        )
    if src["balance"] < amount:
        return "Error: 잔액이 부족합니다."

    ctx.connection.execute(
        "UPDATE accounts SET balance = balance - ?, daily_transferred = daily_transferred + ? "
        "WHERE account_id = ?",
        (amount, amount, from_account),
    )
    ctx.connection.execute(
        "UPDATE accounts SET balance = balance + ? WHERE account_id = ?",
        (amount, to_account),
    )
    cur = ctx.connection.execute(
        "INSERT INTO transfers (from_account, to_account, amount, status) VALUES (?, ?, ?, ?)",
        (from_account, to_account, amount, "completed"),
    )
    ctx.connection.commit()
    transfer_id = cur.lastrowid
    summary = {
        "transfer_id": transfer_id,
        "from_account": mask_account_id(from_account),
        "to_account": mask_account_id(to_account),
        "amount_krw": amount,
        "status": "completed",
    }
    return mask_pii(json.dumps(summary, ensure_ascii=False))


def _escalate(arguments: dict[str, Any], ctx: SessionContext) -> str:
    reason = str(arguments.get("reason", "")).strip() or "사유 미기재"
    ctx.stop_reason = "escalated"
    return mask_pii(f"상담원에게 이관했습니다. 사유: {reason}")


def _wipe_customer(arguments: dict[str, Any], ctx: SessionContext) -> str:
    del arguments, ctx
    return "Error: 이 작업은 금지되어 있습니다."


EXECUTORS: dict[str, ToolFn] = {
    "search_policy": _search_policy,
    "lookup_balance": _lookup_balance,
    "transfer": _transfer,
    "escalate": _escalate,
    "wipe_customer": _wipe_customer,
}


def tool_schemas_for_session(verified: bool) -> list[dict[str, Any]]:
    """세션 권한에 따라 모델에 노출할 tool 스키마를 고른다."""
    common = [
        {
            "name": "search_policy",
            "description": "이체·본인확인 정책 문서를 검색한다.",
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
        {
            "name": "escalate",
            "description": "한도 초과·분쟁·정책 예외 등 상담원 이관이 필요할 때 호출한다.",
            "input_schema": {
                "type": "object",
                "properties": {"reason": {"type": "string"}},
                "required": ["reason"],
            },
        },
    ]
    if not verified:
        return common

    return common + [
        {
            "name": "lookup_balance",
            "description": "본인 명의 계좌 잔액과 당일 이체 누적을 조회한다. 계좌번호는 마스킹되어 반환된다.",
            "input_schema": {
                "type": "object",
                "properties": {"account_id": {"type": "string"}},
                "required": ["account_id"],
            },
        },
        {
            "name": "transfer",
            "description": (
                f"본인 계좌에서 이체한다. 1회 한도 {ONCE_LIMIT_KRW:,}원, "
                f"1일 한도 {DAILY_LIMIT_KRW:,}원. 한도 초과 시 호출하지 말고 escalate 한다."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "from_account": {"type": "string"},
                    "to_account": {"type": "string"},
                    "amount_krw": {"type": "integer"},
                },
                "required": ["from_account", "to_account", "amount_krw"],
            },
        },
        {
            "name": "wipe_customer",
            "description": "고객 데이터를 삭제한다. (금지됨 — 호출해도 거부된다)",
            "input_schema": {
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"],
            },
        },
    ]
