"""Lab 14 - Human in the loop (starter).

Goal: Put a person in the path of an agent's actions: classify every
action as automatic, needing confirmation, or forbidden; enforce that
classification in code; and render a diff so the approver sees what will
actually change.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-3-autonomy/14-human-in-the-loop/tests -v
"""

from __future__ import annotations

import difflib
from typing import Any, Callable

# TODO: step 1. Map each tool name to 'auto', 'confirm', or 'forbidden'.
# Comment the reversibility / blast-radius reason for every entry. Keep the
# whole policy in this one place.
POLICY: dict[str, str] = {}

# In-memory files so executors stay deterministic and offline.
FILES: dict[str, str] = {
    "notes.txt": "alpha\nbeta\ngamma\n",
}

EXECUTORS: dict[str, Callable[[dict[str, Any]], str]] = {}


def classify_action(name: str, arguments: dict[str, Any]) -> str:
    """Return 'auto', 'confirm', or 'forbidden' for one action."""
    # TODO: step 2. Look the tool up in POLICY. An unknown tool defaults to
    # 'confirm', never 'auto': a tool nobody classified is a tool nobody
    # thought about.
    raise NotImplementedError


def render_diff(before: str, after: str, path: str) -> str:
    """Show exactly what a write would change."""
    # TODO: step 3. Use difflib.unified_diff. The approver needs the
    # consequence, not the tool name.
    raise NotImplementedError


def approve(action: dict[str, Any], approver: Callable[[str], bool]) -> bool:
    """Present an action for approval and return the decision."""
    # TODO: step 4. For write_file, append the unified diff. For send_email,
    # show to / subject / body as the consequence. Take the decision through
    # the approver callback so tests can script yes and no.
    raise NotImplementedError


def guarded_execute(
    action: dict[str, Any],
    approver: Callable[[str], bool],
    *,
    actor: str = "approver",
) -> dict[str, Any]:
    """Enforce the policy around one action and return an audit record."""
    # TODO: step 5. Forbidden is refused before anyone is prompted. Return
    # {'executed', 'classification', 'reason', 'result', 'decided_by'} on
    # every path. decided_by is 'policy' for auto/forbidden, or actor for
    # confirm approve/deny.
    raise NotImplementedError


def as_tool_result(record: dict[str, Any], tool_use_id: str) -> dict[str, Any]:
    """Turn an audit record into a tool_result block."""
    # TODO: step 6. On success, content is the result and is_error is False.
    # On refusal, content includes the classification and reason, is_error
    # is True — so a denial becomes information for the model.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Drive one action down each policy path, print the
    # audit record (including decided_by), and show as_tool_result output.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
