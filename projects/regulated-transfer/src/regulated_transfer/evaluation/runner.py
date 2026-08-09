"""오프라인 action-level 평가 — 거절·이관도 성공.

Purpose
    모델 없이 tool 게이트가 기대한 대로 막는지 케이스 JSON으로 검증한다.

Why
    「항상 도와줌」이 아니라 정책상 거절·인간 이관이 pass로 잡히는지
    확인해 보는 연습이다.

Trade-offs
    자연어 품질은 보지 않는다. 실행/차단/에스컬레이션 결과만 본다.

Edges
    expected.outcome: transferred | blocked | escalated | denied_by_human
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from regulated_transfer.packaging.config import EVAL_CASES
from regulated_transfer.tools_gate import db
from regulated_transfer.tools_gate.policy_gate import run_tool
from regulated_transfer.tools_gate.session import SessionContext


def load_cases(path: Path | None = None) -> list[dict[str, Any]]:
    return json.loads((path or EVAL_CASES).read_text(encoding="utf-8"))


def _approver_for(case: dict[str, Any]) -> Callable[[str], bool]:
    mode = case.get("approver", "approve")
    if mode == "deny":
        return lambda _prompt: False
    return lambda _prompt: True


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    """단일 케이스를 실행하고 판정한다."""
    conn = db.connect()
    ctx = SessionContext(
        customer_id=case["customer_id"],
        verified=bool(case.get("verified", True)),
        connection=conn,
    )
    approver = _approver_for(case)
    action = case["action"]
    record = run_tool(action["name"], action.get("arguments") or {}, ctx, approver)

    expected = case["expected"]
    outcome = _infer_outcome(record, ctx)
    ok = outcome == expected["outcome"]
    if "executed" in expected and record["executed"] != expected["executed"]:
        ok = False
    if expected.get("result_contains"):
        if expected["result_contains"] not in str(record.get("result", "")):
            ok = False

    return {
        "id": case["id"],
        "ok": ok,
        "outcome": outcome,
        "expected": expected["outcome"],
        "record": record,
        "stop_reason": ctx.stop_reason,
        "audit_len": len(ctx.audit_events),
        "title": case.get("title", ""),
    }


def _infer_outcome(record: dict[str, Any], ctx: SessionContext) -> str:
    if ctx.stop_reason == "escalated" or record.get("name") == "escalate" and record.get("executed"):
        return "escalated"
    if record.get("classification") == "forbidden" or (
        not record.get("executed") and record.get("reason") == "정책상 금지된 작업입니다."
    ):
        return "blocked"
    if not record.get("approved") and record.get("classification") == "confirm":
        return "denied_by_human"
    if record.get("executed") and record.get("name") == "transfer":
        return "transferred"
    if not record.get("executed"):
        return "blocked"
    return "ok"


def run_eval(path: Path | None = None) -> dict[str, Any]:
    """전체 케이스를 돌리고 요약한다."""
    results = [run_case(c) for c in load_cases(path)]
    passed = sum(1 for r in results if r["ok"])
    return {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }
