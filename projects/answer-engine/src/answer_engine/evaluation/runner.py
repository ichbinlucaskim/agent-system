"""Grounding evaluation — score evidence and citations, not prose polish.

Purpose
    Offline suite that checks abstain, retrieved docs, and citation ids.

Why
    Case 02's defining failure is a fluent answer that outruns evidence. Eval
    therefore treats documents and ``[doc#n]`` markers as the oracle, not a
    judge model's opinion of helpfulness.

Trade-offs
    ``answer_must_contain_any`` also scans passage text so offline stitch still
    passes when the first sentence omits a keyword. That softens lexical checks.

Edges
    Missing case fields are treated as no constraint. Suite rebuilds one shared
    index for all cases.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from answer_engine.packaging.config import Config
from answer_engine.paths import EVAL_CASES
from answer_engine.pipeline import answer_question
from answer_engine.retrieval import CorpusIndex
from answer_engine.synthesis import document_of


def load_cases(path: Path | None = None) -> list[dict[str, Any]]:
    """Load labelled eval cases from JSON.

    Purpose
        Provide the regression set for grounding behaviour.

    Why
        JSON keeps labels editable without code changes.

    Trade-offs
        No schema validation beyond runtime KeyError on bad cases.

    Edges
        Default path is ``data/eval/cases.json``.
    """
    return json.loads((path or EVAL_CASES).read_text(encoding="utf-8"))


def check_case(result: dict[str, Any], case: dict[str, Any]) -> tuple[bool, str]:
    """Score one pipeline result against one case.

    Purpose
        Return (passed, reason) for reporting.

    Why
        Separating check from run keeps suite logic readable in review.

    Trade-offs
        Needle search in passages can pass when the spoken answer omitted the
        word—acceptable for offline stitch, weaker for live answers.

    Edges
        ``expect_abstain`` short-circuits other checks.
    """
    if case.get("expect_abstain"):
        if result.get("abstained"):
            return (True, "abstained")
        return (False, "expected abstain")

    answer = result.get("answer", "")
    for needle in case.get("answer_must_contain_any", []):
        if needle.lower() not in answer.lower():
            blob = answer + " " + " ".join(p["text"] for p in result.get("passages", []))
            if needle.lower() not in blob.lower():
                return (False, f"missing {needle!r}")

    cited_docs = set(result.get("cited_docs") or [])
    passage_docs = {p["doc_id"] for p in result.get("passages", [])}
    for doc in case.get("must_cite_docs", []):
        if doc in cited_docs:
            continue
        if doc in passage_docs and any(
            document_of(c) == doc for c in result.get("citations", [])
        ):
            continue
        return (False, f"missing citation/doc {doc}")

    for doc in case.get("relevant_docs", []):
        if doc not in passage_docs and doc not in cited_docs:
            return (False, f"relevant doc {doc} not retrieved")

    return (True, "ok")


def run_case(case: dict[str, Any], index: CorpusIndex | None = None) -> dict[str, Any]:
    """Execute one case offline and return a compact report row.

    Purpose
        Drive ``answer_question(..., offline=True)`` for deterministic scoring.

    Why
        Offline path exercises retrieval/ranking/assembly without API spend.

    Trade-offs
        Does not measure live model citation obedience.

    Edges
        Builds a fresh index when none is passed (slower if called in a loop
        without sharing).
    """
    index = index or CorpusIndex.build()
    config = Config(api_key="offline", top_k=3, min_score=0.02)
    result = answer_question(case["question"], index, config, offline=True)
    ok, reason = check_case(result, case)
    return {
        "id": case["id"],
        "passed": ok,
        "reason": reason,
        "intent": result.get("intent"),
        "cited_docs": result.get("cited_docs"),
        "passage_docs": [p["doc_id"] for p in result.get("passages", [])],
        "abstained": result.get("abstained"),
    }


def run_suite_offline(cases: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Run every case once and aggregate pass rate.

    Purpose
        Single entry for README / CI offline regression.

    Why
        Shared index across cases avoids repeated chunk/embed cost.

    Trade-offs
        One run each—no flaky multi-trial reporting (unlike lab 15 live suites).

    Edges
        Empty cases list → pass_rate 0.0.
    """
    cases = cases or load_cases()
    index = CorpusIndex.build()
    results = [run_case(case, index) for case in cases]
    passed = sum(1 for r in results if r["passed"])
    return {
        "total": len(results),
        "passed": passed,
        "pass_rate": passed / len(results) if results else 0.0,
        "results": results,
    }
