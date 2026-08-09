"""경로·한도·예산 상수.

Purpose
    프로젝트 루트·데이터 경로와 이체 한도·에이전트 예산을 한곳에 둔다.

Why
    한도 숫자를 README·정책문서·tool 사전조건이 같은 소스를 보게 한다.

Trade-offs
    실무에서는 코어뱅킹/정책 서비스에서 읽어오지만, 연습용으로 상수로 둔다.

Edges
    한도 변경 시 eval 케이스의 expected도 함께 맞춰야 한다.
"""

from __future__ import annotations

from pathlib import Path

# packaging/ → regulated_transfer/ → src/ → project root
ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
POLICY_DIR = DATA_DIR / "policy"
SEED_SQL = DATA_DIR / "seed.sql"
EVAL_CASES = DATA_DIR / "eval" / "cases.json"

# 1회 / 1일 이체 한도 (원)
ONCE_LIMIT_KRW = 1_000_000
DAILY_LIMIT_KRW = 3_000_000

AGENT_MAX_STEPS = 8
AGENT_MAX_TOOL_CALLS = 12
AGENT_WALL_CLOCK_S = 90.0
