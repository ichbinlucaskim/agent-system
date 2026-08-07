"""Filesystem anchors for data shipped with the package.

Purpose
    Centralize paths to seed SQL, policy markdown, and eval cases so tools,
    retrieval, and evaluation do not hard-code relative locations.

Why
    Lab packaging lesson: data lives next to the project, not beside every
    caller. One module keeps install layout and tests aligned.

Trade-offs
    ``PACKAGE_ROOT`` is two parents above this file (``src/`` → project root).
    That assumes the current source layout; a wheel install that relocates
    data would need a different discovery strategy.

Edges
    Paths are ``Path`` objects only—callers must ``read_text`` / ``exists``
    themselves. Missing files surface as ordinary OS errors at use time.
"""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PACKAGE_ROOT / "data"
POLICY_DIR = DATA_DIR / "policy"
SEED_SQL = DATA_DIR / "seed.sql"
EVAL_CASES = DATA_DIR / "eval" / "cases.json"
