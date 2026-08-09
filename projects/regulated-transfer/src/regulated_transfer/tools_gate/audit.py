"""감사 로그 — 세션 버퍼 + SQLite.

Purpose
    tool/HITL 결정을 마스킹된 payload와 함께 남긴다.

Why
    「누가 승인했는지, 어떤 사전조건이 돌았는지」를 한 이체 단위로 다시 읽을 수 있게 한다.

Trade-offs
    연습용이라 구조화 필드는 최소. 실무는 불변 감사 스토어·서명·보존기간이 붙는다.

Edges
    payload는 항상 mask_pii 후 JSON으로 저장한다. 계좌 원문 금지.
"""

from __future__ import annotations

import json
from typing import Any

from regulated_transfer.tools_gate.pii import mask_pii
from regulated_transfer.tools_gate.session import SessionContext


def append_audit(
    ctx: SessionContext,
    *,
    event_type: str,
    tool_name: str | None,
    decided_by: str,
    classification: str | None,
    executed: bool,
    reason: str,
    payload: dict[str, Any],
) -> None:
    """세션 버퍼와 DB에 감사 이벤트를 추가한다."""
    safe_payload = mask_pii(json.dumps(payload, ensure_ascii=False))
    event = {
        "event_type": event_type,
        "tool_name": tool_name,
        "decided_by": decided_by,
        "classification": classification,
        "executed": executed,
        "reason": mask_pii(reason),
        "payload": json.loads(safe_payload),
    }
    ctx.audit_events.append(event)
    ctx.connection.execute(
        """
        INSERT INTO audit_log
            (event_type, tool_name, decided_by, classification, executed, reason, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_type,
            tool_name,
            decided_by,
            classification,
            1 if executed else 0,
            event["reason"],
            safe_payload,
        ),
    )
    ctx.connection.commit()
