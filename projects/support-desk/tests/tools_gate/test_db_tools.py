"""Offline tests for db and tool preconditions."""

from __future__ import annotations

import tempfile

from support_desk.tools_gate.db import get_order, init_db
from support_desk.tools_gate.retrieve import build_policy_store
from support_desk.tools_gate.tools import (
    ToolContext,
    cancel_order_tool,
    issue_refund_tool,
    lookup_order_tool,
)


def _ctx():
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    tmp.close()
    return ToolContext(init_db(tmp.name), build_policy_store())


def test_lookup_order_wraps_untrusted():
    ctx = _ctx()
    result = lookup_order_tool(ctx, {"order_id": "ORD-100"})
    assert "untrusted-content" in result
    assert "ORD-100" in result


def test_refund_ok_within_window():
    ctx = _ctx()
    result = issue_refund_tool(
        ctx, {"order_id": "ORD-100", "amount_usd": 49.99}
    )
    assert not result.startswith("Error:")
    assert get_order(ctx.connection, "ORD-100")["status"] == "refunded"


def test_refund_rejects_expired_window():
    ctx = _ctx()
    result = issue_refund_tool(
        ctx, {"order_id": "ORD-200", "amount_usd": 120.0}
    )
    assert result.startswith("Error:")
    assert "30-day" in result
    assert get_order(ctx.connection, "ORD-200")["status"] == "delivered"


def test_cancel_rejects_shipped():
    ctx = _ctx()
    result = cancel_order_tool(ctx, {"order_id": "ORD-300"})
    assert result.startswith("Error:")
    assert get_order(ctx.connection, "ORD-300")["status"] == "shipped"


def test_cancel_processing_ok():
    ctx = _ctx()
    result = cancel_order_tool(ctx, {"order_id": "ORD-400"})
    assert not result.startswith("Error:")
    assert get_order(ctx.connection, "ORD-400")["status"] == "cancelled"
