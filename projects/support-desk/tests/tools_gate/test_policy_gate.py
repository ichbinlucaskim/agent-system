"""HITL and forbidden enforcement."""

from __future__ import annotations

import tempfile

from support_desk.tools_gate.db import get_order, init_db
from support_desk.tools_gate.policy_gate import classify_action, guarded_execute
from support_desk.tools_gate.retrieve import build_policy_store
from support_desk.tools_gate.tools import ToolContext


def _ctx():
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    tmp.close()
    return ToolContext(init_db(tmp.name), build_policy_store())


def test_wipe_is_forbidden_even_if_approver_says_yes():
    ctx = _ctx()
    record = guarded_execute(
        {"name": "wipe_account", "arguments": {"customer_id": "C-1"}},
        ctx,
        approver=lambda prompt: True,
    )
    assert record["classification"] == "forbidden"
    assert record["executed"] is False
    assert record["decided_by"] == "policy"


def test_refund_confirm_denied():
    ctx = _ctx()
    record = guarded_execute(
        {"name": "issue_refund", "arguments": {"order_id": "ORD-100", "amount_usd": 49.99}},
        ctx,
        approver=lambda prompt: False,
    )
    assert record["classification"] == "confirm"
    assert record["executed"] is False
    assert get_order(ctx.connection, "ORD-100")["status"] == "delivered"


def test_refund_confirm_approved():
    ctx = _ctx()
    record = guarded_execute(
        {"name": "issue_refund", "arguments": {"order_id": "ORD-100", "amount_usd": 49.99}},
        ctx,
        approver=lambda prompt: True,
    )
    assert record["executed"] is True
    assert record["decided_by"] == "approver"
    assert get_order(ctx.connection, "ORD-100")["status"] == "refunded"


def test_classify_lookup_auto():
    assert classify_action("lookup_order") == "auto"
    assert classify_action("issue_refund") == "confirm"
    assert classify_action("wipe_account") == "forbidden"
