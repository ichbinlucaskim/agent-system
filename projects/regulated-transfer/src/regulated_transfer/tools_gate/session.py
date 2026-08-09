"""세션 컨텍스트 — 본인확인 여부가 tool 노출을 가른다.

Purpose
    요청마다 고객 ID·verified 플래그·감사 버퍼를 담는다.

Why
    미확인 세션에 이체 tool을 주면 프롬프트 인젝션으로 한도 우회 시도 면적이 생긴다.

Trade-offs
    실무의 세션/토큰 검증을 bool 하나로 축소했다.

Edges
    verified=False이면 잔액조회·이체 스키마가 에이전트에게 안 보인다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionContext:
    """한 통화/세션의 권한·감사 상태."""

    customer_id: str
    verified: bool
    connection: Any
    audit_events: list[dict[str, Any]] = field(default_factory=list)
    stop_reason: str | None = None
