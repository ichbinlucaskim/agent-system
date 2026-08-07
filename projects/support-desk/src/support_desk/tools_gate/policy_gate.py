"""Human-in-the-loop classification and guarded execution (lab 14)."""

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
