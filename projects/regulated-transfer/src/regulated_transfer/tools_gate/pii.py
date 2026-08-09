"""주민번호·계좌번호 마스킹.

Purpose
    tool 결과와 감사 로그에 넣을 문자열에서 PII를 가린다.

Why
    모델/로그가 원문을 들고 다니면 유출 면적이 커진다.
    권한·데이터 취급을 코드에 남기는 최소 연습이다.

Trade-offs
    정규식 기반이라 형식이 다르면 놓칠 수 있다. 실무는 필드 단위 마스킹이 낫다.

Edges
    이미 마스킹된 문자열을 다시 넣어도 깨지지 않게 보수적으로 동작한다.
"""

from __future__ import annotations

import re

# 900101-1234567 / 9001011234567
_RRN = re.compile(r"\b(\d{6})-?(\d{7})\b")
# 110-123-456789 형태 (하이픈 포함 계좌)
_ACCOUNT = re.compile(r"\b(\d{2,3})-(\d{2,4})-(\d{4,})\b")


def mask_rrn(value: str) -> str:
    """주민등록번호 뒷자리를 가린다."""

    def _repl(m: re.Match[str]) -> str:
        return f"{m.group(1)}-*******"

    return _RRN.sub(_repl, value)


def mask_account(value: str) -> str:
    """계좌번호 앞·뒤를 일부만 남긴다."""

    def _repl(m: re.Match[str]) -> str:
        last = m.group(3)
        tail = last[-4:] if len(last) >= 4 else last
        return f"{m.group(1)}-****-{tail}"

    return _ACCOUNT.sub(_repl, value)


def mask_pii(text: str) -> str:
    """로그·tool 결과에 넣기 전 일괄 마스킹."""
    return mask_account(mask_rrn(text))


def mask_account_id(account_id: str) -> str:
    """계좌 ID 필드 전용 마스킹."""
    return mask_account(account_id) if "-" in account_id else f"****{account_id[-4:]}"
