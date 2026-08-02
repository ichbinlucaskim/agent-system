"""Lab 14 - Human in the loop (starter).

Goal: Put a person in the path of an agent's actions: classify every action as automatic, needing confirmation, or forbidden; enforce that classification in code; and render a diff so the approver sees what will actually change.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-3-autonomy/14-human-in-the-loop/tests -v
"""

from __future__ import annotations

from typing import Any, Callable


def classify_action(name: str, arguments: dict[str, Any]) -> str:
    """Return 'auto', 'confirm', or 'forbidden' for one action."""
    # TODO: step 2. Look the tool up in POLICY. An unknown tool defaults to 'confirm', never 'auto': a tool nobody classified is a tool nobody thought about.
    raise NotImplementedError


def render_diff(before: str, after: str, path: str) -> str:
    """Show exactly what a write would change."""
    # TODO: step 3. Use difflib.unified_diff. The approver needs the consequence, not the tool name; a confirmation without a diff trains people to click approve.
    raise NotImplementedError


def approve(action: dict[str, Any], approver: Callable[[str], bool]) -> bool:
    """Present an action for approval and return the decision."""
    # TODO: step 4. Render a diff for writes. Take the decision through a callback so tests can script both yes and no.
    raise NotImplementedError


def guarded_execute(action: dict[str, Any], approver: Callable[[str], bool]) -> dict[str, Any]:
    """Enforce the policy around one action and return an audit record."""
    # TODO: step 5. Forbidden is refused before anyone is prompted. Return {'executed': bool, 'classification': ..., 'reason': ..., 'result': ...} on every path, including refusals.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
