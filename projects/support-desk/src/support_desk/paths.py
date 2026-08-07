"""Filesystem anchors for data shipped with the package."""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PACKAGE_ROOT / "data"
POLICY_DIR = DATA_DIR / "policy"
SEED_SQL = DATA_DIR / "seed.sql"
EVAL_CASES = DATA_DIR / "eval" / "cases.json"
