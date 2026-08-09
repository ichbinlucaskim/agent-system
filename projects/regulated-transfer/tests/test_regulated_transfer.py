"""규제이체 데스크 테스트 — 모델 없이 게이트·PII·eval."""

from __future__ import annotations

from regulated_transfer.evaluation.runner import run_eval
from regulated_transfer.tools_gate import db
from regulated_transfer.tools_gate.pii import mask_account_id, mask_pii, mask_rrn
from regulated_transfer.tools_gate.policy_gate import run_tool
from regulated_transfer.tools_gate.session import SessionContext
from regulated_transfer.tools_gate.tools import tool_schemas_for_session


def test_mask_rrn_and_account():
    assert "1234567" not in mask_rrn("900101-1234567")
    assert "900101" in mask_rrn("900101-1234567")
    masked = mask_account_id("110-123-456789")
    assert "110-123-456789" not in masked
    assert masked.endswith("6789")


def test_tool_result_masks_pii():
    conn = db.connect()
    ctx = SessionContext(customer_id="C-100", verified=True, connection=conn)
    out = run_tool("search_policy", {"query": "한도"}, ctx, lambda _p: True)
    assert out["executed"]
    assert "900101-1234567" not in out["result"]


def test_unverified_session_hides_transfer_tools():
    names = {t["name"] for t in tool_schemas_for_session(False)}
    assert "transfer" not in names
    assert "lookup_balance" not in names
    assert "escalate" in names


def test_once_limit_blocks_even_if_approver_says_yes():
    conn = db.connect()
    ctx = SessionContext(customer_id="C-100", verified=True, connection=conn)
    record = run_tool(
        "transfer",
        {
            "from_account": "110-123-456789",
            "to_account": "110-987-654321",
            "amount_krw": 2_000_000,
        },
        ctx,
        lambda _p: True,
    )
    assert record["executed"] is False
    assert "1회 이체 한도" in record["result"]


def test_audit_payload_has_no_full_account():
    conn = db.connect()
    ctx = SessionContext(customer_id="C-100", verified=True, connection=conn)
    run_tool(
        "transfer",
        {
            "from_account": "110-123-456789",
            "to_account": "110-987-654321",
            "amount_krw": 10_000,
        },
        ctx,
        lambda _p: True,
    )
    blob = mask_pii(str(ctx.audit_events))
    assert "110-123-456789" not in blob


def test_eval_suite_all_pass():
    summary = run_eval()
    failed = [r for r in summary["results"] if not r["ok"]]
    assert failed == [], failed


def test_refusal_and_escalation_count_as_pass():
    """거절·이관 케이스가 명시적으로 pass인지 확인한다."""
    summary = run_eval()
    by_id = {r["id"]: r for r in summary["results"]}
    assert by_id["E02"]["ok"] and by_id["E02"]["outcome"] == "blocked"
    assert by_id["E04"]["ok"] and by_id["E04"]["outcome"] == "blocked"
    assert by_id["E05"]["ok"] and by_id["E05"]["outcome"] == "escalated"
    assert by_id["E06"]["ok"] and by_id["E06"]["outcome"] == "denied_by_human"
