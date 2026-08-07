"""Filesystem anchors for packaged data.

Purpose
    Resolve corpus and eval paths relative to the project root.

Why
    Avoids cwd-dependent opens when the package is imported from tests or CLI.

Trade-offs
    Assumes the installed layout still has ``data/`` next to the project root
    (``parents[2]`` from ``src/answer_engine/paths.py``).

Edges
    Broken installs with missing data/ fail at first read, not at import.
"""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PACKAGE_ROOT / "data"
CORPUS_DIR = DATA_DIR / "corpus"
EVAL_CASES = DATA_DIR / "eval" / "cases.json"
