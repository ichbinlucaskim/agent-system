"""Human-in-the-loop classification and guarded tool execution (lab 14).

Purpose
    Classify each tool as auto, confirm, or forbidden; prompt an approver for
    irreversible actions; execute only when policy and humans allow; and shape
    Anthropic ``tool_result`` blocks from audit records.

Why
    This is the tools_gate permission layer: reversibility and blast radius
    decide the class, not how helpful the tool name sounds. Side effects that
    move money or cancel orders cannot rely on the model alone.

Trade-offs
    Classification is name-based today (``arguments`` reserved for later).
    Default CLI/eval approvers can auto-approve, which exercises the confirm
    path without a human—useful for smoke, unsafe if left on in production.

Edges
    Forbidden tools never call executors. Denied confirms return
    ``executed=False`` with a refusal reason. Executor ``Error:`` prefixes mark
    ``executed=False`` even after approval.
"""

from __future__ import annotations

from typing import Any, Callable

from support_desk.tools_gate.tools import EXECUTORS, ToolContext

# Classification is by reversibility and blast radius, not by how the tool sounds.
POLICY: dict[str, str] = {
    "search_policy": "auto",
    "lookup_order": "auto",
    "escalate": "auto",
    "issue_refund": "confirm",
    "cancel_order": "confirm",
    "wipe_account": "forbidden",
}


def classify_action(name: str, arguments: dict[str, Any] | None = None) -> str:
    """Map a tool name to auto, confirm, or forbidden.

    Purpose
        Return the HITL class for one proposed action.

    Why
        Keeps permission policy in one table so the agent loop stays free of
        per-tool if/else.

    Trade-offs
        Unknown names default to ``forbidden`` (fail closed). Argument-sensitive
        rules are stubbed via ``del arguments`` for a future extension.

    Edges
        ``arguments`` is currently ignored.
    """
    del arguments  # reserved for argument-sensitive policies later
    return POLICY.get(name, "forbidden")


def _consequence_lines(name: str, arguments: dict[str, Any], ctx: ToolContext) -> list[str]:
    if name == "issue_refund":
        order_id = str(arguments.get("order_id", "")).upper()
        amount = arguments.get("amount_usd")
        from support_desk.tools_gate import db

        order = db.get_order(ctx.connection, order_id)
        lines = [
            f"refund order {order_id} for {amount} USD",
            f"current status: {order['status'] if order else 'unknown'}",
            f"order total: {order['total_usd'] if order else 'unknown'}",
        ]
        return lines
    if name == "cancel_order":
        return [f"cancel order {str(arguments.get('order_id', '')).upper()}"]
    return [f"arguments: {arguments}"]


def approve(action: dict[str, Any], approver: Callable[[str], bool], ctx: ToolContext) -> bool:
    """Ask the approver whether a confirm-class action may proceed.

    Purpose
        Build a short consequence summary and delegate the yes/no decision.

    Why
        Humans need concrete blast-radius text (order id, amount, status), not
        only the tool name.

    Trade-offs
        Approver API is a single prompt string → bool; no structured UI.

    Edges
        Summary always starts with ``approve {name}?``. Missing orders show
        status/total as ``unknown``.
    """
    name = action["name"]
    arguments = dict(action.get("arguments", {}))
    summary = [f"approve {name}?"]
    summary.extend(_consequence_lines(name, arguments, ctx))
    return bool(approver("\n".join(summary)))


def guarded_execute(
    action: dict[str, Any],
    ctx: ToolContext,
    approver: Callable[[str], bool],
    *,
    actor: str = "approver",
) -> dict[str, Any]:
    """Classify, optionally confirm, then run a tool or return a refusal audit.

    Purpose
        Single entry for every tool attempt from the agent loop or offline eval.

    Why
        Centralizes forbidden / deny / missing-executor paths so callers always
        get a uniform audit dict (executed, classification, reason, result).

    Trade-offs
        ``executed`` is False when the executor returns an ``Error:`` string—
        approval is not the same as business success. ``decided_by`` labels
        policy vs human for reports.

    Edges
        Forbidden → no executor call. Confirm + deny → no executor call.
        Unknown tool name after classification → refusal. Auto path skips
        ``approve``.
    """
    name = action["name"]
    arguments = dict(action.get("arguments", {}))
    classification = classify_action(name, arguments)

    if classification == "forbidden":
        return {
            "executed": False,
            "classification": classification,
            "reason": f"{name} is forbidden by policy and was not attempted.",
            "result": None,
            "decided_by": "policy",
            "name": name,
            "arguments": arguments,
        }

    if classification == "confirm":
        if not approve(action, approver, ctx):
            return {
                "executed": False,
                "classification": classification,
                "reason": f"{name} was denied by the approver.",
                "result": None,
                "decided_by": actor,
                "name": name,
                "arguments": arguments,
            }

    executor = EXECUTORS.get(name)
    if executor is None:
        return {
            "executed": False,
            "classification": classification,
            "reason": f"no executor is registered for {name}.",
            "result": None,
            "decided_by": "policy",
            "name": name,
            "arguments": arguments,
        }

    result = executor(ctx, arguments)
    succeeded = not str(result).startswith("Error:")
    return {
        "executed": succeeded,
        "classification": classification,
        "reason": (
            "auto-approved by policy"
            if classification == "auto"
            else "approved by the approver"
        ),
        "result": result,
        "decided_by": "policy" if classification == "auto" else actor,
        "name": name,
        "arguments": arguments,
    }


def as_tool_result(record: dict[str, Any], tool_use_id: str) -> dict[str, Any]:
    """Convert an audit record into an Anthropic-style tool_result block.

    Purpose
        Feed the model a content string and ``is_error`` flag after each gated
        attempt.

    Why
        The loop must continue after refusals with an explicit error tool
        result, not a silent skip.

    Trade-offs
        Refusal text is synthesized from classification + reason when nothing
        executed. Executor error strings keep their ``Error:`` prefix.

    Edges
        ``is_error`` is True for executor errors and for non-executed refusals.
    """
    result = record.get("result")
    if result is not None and str(result).startswith("Error:"):
        content = str(result)
        is_error = True
    elif record["executed"]:
        content = str(result)
        is_error = False
    else:
        content = f"Action refused ({record['classification']}): {record['reason']}"
        is_error = True
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": content,
        "is_error": is_error,
    }
