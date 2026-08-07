"""Lab 14 - Human in the loop (reference solution).

The gap between a tool_use block and your code executing it is the only
place a person can stand. Every action is classified as automatic,
needing confirmation, or forbidden; the classification is enforced in
code, and the approver is shown the consequence, not the tool name.
"""

from __future__ import annotations

import difflib
from typing import Any, Callable

# Classification is by reversibility and blast radius, not by how the tool
# sounds. The whole policy lives in this one mapping so that widening or
# narrowing it is a deliberate, reviewable change.
POLICY: dict[str, str] = {
    # Reading is reversible and changes nothing, so it runs unprompted.
    "read_file": "auto",
    "list_files": "auto",
    # A write destroys the previous contents, and an email cannot be
    # unsent, so a person sees the consequence first.
    "write_file": "confirm",
    "send_email": "confirm",
    # Dropping production data is not a decision to delegate at all. The
    # executor refuses the name even if a prompt smuggles it in, because a
    # system prompt saying never is only a request.
    "delete_database": "forbidden",
}

# An in-memory file system keeps the executors deterministic and offline.
FILES: dict[str, str] = {
    "notes.txt": "alpha\nbeta\ngamma\n",
}


def _read_file(arguments: dict[str, Any]) -> str:
    path = str(arguments.get("path", ""))
    if path not in FILES:
        return f"Error: no file {path!r}."
    return FILES[path]


def _list_files(arguments: dict[str, Any]) -> str:
    return ", ".join(sorted(FILES))


def _write_file(arguments: dict[str, Any]) -> str:
    path = str(arguments.get("path", ""))
    FILES[path] = str(arguments.get("content", ""))
    return f"Wrote {len(FILES[path])} characters to {path}."


def _send_email(arguments: dict[str, Any]) -> str:
    return f"Sent email to {arguments.get('to', '?')}: {arguments.get('subject', '')}"


EXECUTORS: dict[str, Callable[[dict[str, Any]], str]] = {
    "read_file": _read_file,
    "list_files": _list_files,
    "write_file": _write_file,
    "send_email": _send_email,
    # delete_database deliberately has no executor. Forbidden means the
    # capability does not exist, not that it exists behind a warning.
}


def classify_action(name: str, arguments: dict[str, Any]) -> str:
    """Return 'auto', 'confirm', or 'forbidden' for one action."""
    # An unknown tool defaults to confirm, never auto: a tool nobody
    # classified is a tool nobody thought about.
    return POLICY.get(name, "confirm")


def render_diff(before: str, after: str, path: str) -> str:
    """Show exactly what a write would change."""
    lines = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
    )
    return "".join(lines)


def _consequence_lines(name: str, arguments: dict[str, Any]) -> list[str]:
    """Lines that show what will actually happen if the action runs."""
    if name == "write_file":
        # The approver needs the diff, not the tool name. A confirmation
        # without it trains people to click approve.
        path = str(arguments.get("path", ""))
        before = FILES.get(path, "")
        after = str(arguments.get("content", ""))
        return [render_diff(before, after, path)]
    if name == "send_email":
        # An email cannot be unsent: show recipient and subject up front,
        # not buried inside a raw arguments dump.
        return [
            f"to: {arguments.get('to', '')}",
            f"subject: {arguments.get('subject', '')}",
            f"body: {arguments.get('body', '')}",
        ]
    return []


def approve(action: dict[str, Any], approver: Callable[[str], bool]) -> bool:
    """Present an action for approval and return the decision."""
    name = action["name"]
    arguments = dict(action.get("arguments", {}))
    summary = [f"approve {name}?"]
    summary.extend(_consequence_lines(name, arguments))
    # The decision comes through a callback so tests can script both
    # answers; an interactive main just passes input-based yes or no.
    return bool(approver("\n".join(summary)))


def _audit(
    *,
    executed: bool,
    classification: str,
    reason: str,
    result: Any,
    decided_by: str,
) -> dict[str, Any]:
    """Build the audit record every path must return."""
    return {
        "executed": executed,
        "classification": classification,
        "reason": reason,
        "result": result,
        # When something goes wrong the question is what was approved and
        # by whom; "policy" means no person was in the loop.
        "decided_by": decided_by,
    }


def guarded_execute(
    action: dict[str, Any],
    approver: Callable[[str], bool],
    *,
    actor: str = "approver",
) -> dict[str, Any]:
    """Enforce the policy around one action and return an audit record."""
    name = action["name"]
    arguments = dict(action.get("arguments", {}))
    classification = classify_action(name, arguments)

    # Forbidden is refused before anyone is prompted: this path must not
    # depend on a human being awake, or on the executor existing.
    if classification == "forbidden":
        return _audit(
            executed=False,
            classification=classification,
            reason=f"{name} is forbidden by policy and was not attempted.",
            result=None,
            decided_by="policy",
        )

    if classification == "confirm":
        if not approve(action, approver):
            return _audit(
                executed=False,
                classification=classification,
                reason=f"{name} was denied by the approver.",
                result=None,
                decided_by=actor,
            )

    executor = EXECUTORS.get(name)
    if executor is None:
        return _audit(
            executed=False,
            classification=classification,
            reason=f"no executor is registered for {name}.",
            result=None,
            decided_by="policy",
        )

    result = executor(arguments)
    if classification == "auto":
        return _audit(
            executed=True,
            classification=classification,
            reason="auto-approved by policy",
            result=result,
            decided_by="policy",
        )
    return _audit(
        executed=True,
        classification=classification,
        reason="approved by the approver",
        result=result,
        decided_by=actor,
    )


def as_tool_result(record: dict[str, Any], tool_use_id: str) -> dict[str, Any]:
    """Turn an audit record into a tool_result block.

    A refused action goes back to the model with its reason, so a denial
    becomes information the model can act on rather than a dead end.
    """
    if record["executed"]:
        content = str(record["result"])
    else:
        content = f"Action refused ({record['classification']}): {record['reason']}"
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": content,
        "is_error": not record["executed"],
    }


def main() -> int:
    """Run one action down each policy path and print the audit records."""

    def approve_all(prompt: str) -> bool:
        print(prompt)
        print("(scripted approver says yes)\n")
        return True

    def deny_all(prompt: str) -> bool:
        print(prompt)
        print("(scripted approver says no)\n")
        return False

    actions: list[tuple[dict[str, Any], Callable[[str], bool]]] = [
        ({"name": "read_file", "arguments": {"path": "notes.txt"}}, deny_all),
        (
            {
                "name": "write_file",
                "arguments": {"path": "notes.txt", "content": "alpha\nBETA\ngamma\n"},
            },
            approve_all,
        ),
        (
            {
                "name": "send_email",
                "arguments": {
                    "to": "team@example.com",
                    "subject": "Weekly report",
                    "body": "Status update.",
                },
            },
            deny_all,
        ),
        ({"name": "delete_database", "arguments": {"env": "production"}}, approve_all),
    ]

    for index, (action, approver) in enumerate(actions):
        record = guarded_execute(action, approver, actor="demo-approver")
        print(
            f"{action['name']:<16} class={record['classification']:<10} "
            f"executed={record['executed']} decided_by={record['decided_by']} "
            f"reason={record['reason']}"
        )
        print(f"as tool result: {as_tool_result(record, f'toolu_{index}')}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
