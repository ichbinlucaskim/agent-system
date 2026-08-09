"""HITL 분류와 가드된 tool 실행.

Purpose
    auto / confirm / forbidden으로 나누고, 승인 후에만 executor를 호출한다.

Why
    이체는 되돌리기 어렵다. 모델 혼자 끝내지 못하게 인간(또는 대체 승인자)을 끼운다.

Trade-offs
    CLI/eval 기본 승인자는 자동 승인할 수 있어 스모크에는 편하고 운영에는 위험하다.

Edges
    forbidden은 executor를 호출하지 않는다. 사전조건 Error: 는 executed=False.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from regulated_transfer.tools_gate.audit import append_audit
from regulated_transfer.tools_gate.pii import mask_account_id, mask_pii
from regulated_transfer.tools_gate.session import SessionContext
from regulated_transfer.tools_gate.tools import EXECUTORS

POLICY: dict[str, str] = {
    "search_policy": "auto",
    "lookup_balance": "auto",
    "escalate": "auto",
    "transfer": "confirm",
    "wipe_customer": "forbidden",
}


def classify_action(name: str, arguments: dict[str, Any] | None = None) -> str:
    """tool 이름을 auto/confirm/forbidden으로 분류한다."""
    del arguments
    return POLICY.get(name, "forbidden")


def _consequence_lines(name: str, arguments: dict[str, Any]) -> list[str]:
    if name == "transfer":
        return [
            f"출금: {mask_account_id(str(arguments.get('from_account', '')))}",
            f"입금: {mask_account_id(str(arguments.get('to_account', '')))}",
            f"금액: {arguments.get('amount_krw')}원",
        ]
    return [mask_pii(f"인자: {arguments}")]


def approve(
    action: dict[str, Any],
    approver: Callable[[str], bool],
    ctx: SessionContext,
) -> bool:
    """confirm 등급의 결과를 승인자에게 묻고 감사에 남긴다."""
    name = action["name"]
    arguments = action.get("arguments") or {}
    prompt = "다음 이체/작업을 승인합니까?\n" + "\n".join(
        f"- {line}" for line in _consequence_lines(name, arguments)
    )
    ok = bool(approver(prompt))
    append_audit(
        ctx,
        event_type="hitl_decision",
        tool_name=name,
        decided_by="human_approver" if ok else "human_approver_denied",
        classification="confirm",
        executed=False,
        reason="승인" if ok else "거부",
        payload={"arguments": _safe_args(name, arguments), "prompt": mask_pii(prompt)},
    )
    return ok


def _safe_args(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    out = dict(arguments)
    if name == "transfer":
        if "from_account" in out:
            out["from_account"] = mask_account_id(str(out["from_account"]))
        if "to_account" in out:
            out["to_account"] = mask_account_id(str(out["to_account"]))
    return out


def run_tool(
    name: str,
    arguments: dict[str, Any],
    ctx: SessionContext,
    approver: Callable[[str], bool],
) -> dict[str, Any]:
    """분류 → (필요 시) 승인 → 실행 → 감사 레코드."""
    classification = classify_action(name, arguments)
    safe_args = _safe_args(name, arguments)

    if classification == "forbidden":
        record = {
            "name": name,
            "classification": classification,
            "approved": False,
            "executed": False,
            "reason": "정책상 금지된 작업입니다.",
            "result": "Error: 정책상 금지된 작업입니다.",
        }
        append_audit(
            ctx,
            event_type="tool_blocked",
            tool_name=name,
            decided_by="policy_gate",
            classification=classification,
            executed=False,
            reason=record["reason"],
            payload={"arguments": safe_args},
        )
        return record

    if classification == "confirm":
        if not approve({"name": name, "arguments": arguments}, approver, ctx):
            record = {
                "name": name,
                "classification": classification,
                "approved": False,
                "executed": False,
                "reason": "승인자 거부",
                "result": "Error: 승인자가 이체를 거부했습니다.",
            }
            append_audit(
                ctx,
                event_type="tool_denied",
                tool_name=name,
                decided_by="human_approver",
                classification=classification,
                executed=False,
                reason=record["reason"],
                payload={"arguments": safe_args},
            )
            return record
        approved = True
        decided_by = "human_approver"
    else:
        approved = True
        decided_by = "policy_auto"

    executor = EXECUTORS.get(name)
    if executor is None:
        result = f"Error: 알 수 없는 tool: {name}"
        executed = False
        reason = "unknown_tool"
    else:
        result = executor(arguments, ctx)
        executed = not str(result).startswith("Error:")
        reason = "ok" if executed else str(result)

    record = {
        "name": name,
        "classification": classification,
        "approved": approved,
        "executed": executed,
        "reason": reason,
        "result": mask_pii(str(result)),
    }
    append_audit(
        ctx,
        event_type="tool_result",
        tool_name=name,
        decided_by=decided_by,
        classification=classification,
        executed=executed,
        reason=reason if len(reason) < 200 else reason[:200],
        payload={"arguments": safe_args, "result": record["result"]},
    )
    return record


def to_tool_result_block(tool_use_id: str, record: dict[str, Any]) -> dict[str, Any]:
    """Anthropic tool_result 블록 형태로 만든다."""
    content = record.get("result") or record.get("reason") or ""
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": mask_pii(str(content)),
        "is_error": not record.get("executed", False),
    }


def audit_story_for_transfer(ctx: SessionContext) -> str:
    """한 건의 이체/시도에 대한 감사 스토리 텍스트."""
    lines = [
        f"고객: {ctx.customer_id}",
        f"본인확인: {'완료' if ctx.verified else '미완료'}",
        f"stop_reason: {ctx.stop_reason or '(없음)'}",
        "이벤트:",
    ]
    for ev in ctx.audit_events:
        lines.append(
            f"  - [{ev['event_type']}] tool={ev.get('tool_name')} "
            f"decided_by={ev.get('decided_by')} executed={ev.get('executed')} "
            f"reason={mask_pii(str(ev.get('reason', '')))}"
        )
    return "\n".join(lines)
