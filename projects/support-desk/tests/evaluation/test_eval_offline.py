"""Offline eval suite and scripted agent loop."""

from __future__ import annotations

from support_desk.evaluation.runner import (
    load_cases,
    run_case_with_scripted_model,
    run_suite_offline,
)


def test_offline_suite_passes():
    report = run_suite_offline()
    assert report["total"] == len(load_cases())
    failed = [r["id"] for r in report["results"] if not r["passed"]]
    assert not failed, f"failed cases: {failed}"
    assert report["pass_rate"] == 1.0


def test_scripted_agent_loop_refund_ok():
    case = next(c for c in load_cases() if c["id"] == "refund_ok")
    result = run_case_with_scripted_model(case)
    assert result["passed"] is True


def test_scripted_injection_blocked():
    case = next(c for c in load_cases() if c["id"] == "injection_ignore_policy")
    result = run_case_with_scripted_model(case)
    assert result["passed"] is True
