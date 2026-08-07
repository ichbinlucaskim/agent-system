"""Tests for Lab 14 - Human in the loop.

Classification, the diff, approval prompts, tool-result wiring, and the
enforcement paths are deterministic; approvals come through a scripted
callback, so every test runs offline without an API key.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load(name: str, path: Path):
    """Load a module by file path.

    The module is registered in sys.modules before execution because
    dataclasses look their own module up by name while being created.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


LAB_ROOT = Path(__file__).resolve().parents[1]
solution = _load("lab14_solution", LAB_ROOT / "solution" / "main.py")


def test_a_forbidden_action_is_never_executed(monkeypatch):
    """Forbidden is refused before the approver or any executor is reached."""
    executed: list[dict] = []
    prompts: list[str] = []

    def recorder(arguments):
        executed.append(arguments)
        return "dropped"

    def approver(prompt):
        prompts.append(prompt)
        return True

    # Even with an executor registered and an approver saying yes, the
    # refusal must happen first.
    monkeypatch.setitem(solution.EXECUTORS, "delete_database", recorder)
    record = solution.guarded_execute(
        {"name": "delete_database", "arguments": {"env": "production"}}, approver
    )
    assert record["executed"] is False
    assert record["classification"] == "forbidden"
    assert record["decided_by"] == "policy"
    assert executed == []
    assert prompts == []


def test_an_unknown_tool_defaults_to_confirm():
    """A tool nobody classified is a tool nobody thought about."""
    assert solution.classify_action("format_disk", {}) == "confirm"


def test_an_auto_action_runs_without_an_approver():
    """An auto action executes even when the approver would deny it."""
    prompts: list[str] = []

    def deny(prompt):
        prompts.append(prompt)
        return False

    record = solution.guarded_execute(
        {"name": "read_file", "arguments": {"path": "notes.txt"}}, deny
    )
    assert record["executed"] is True
    assert record["classification"] == "auto"
    assert record["decided_by"] == "policy"
    assert prompts == []


def test_a_denied_confirmation_does_not_execute():
    """An approver saying no leaves the action unexecuted, with the reason."""

    def deny(prompt):
        return False

    record = solution.guarded_execute(
        {
            "name": "send_email",
            "arguments": {"to": "team@example.com", "subject": "Weekly report"},
        },
        deny,
        actor="alice",
    )
    assert record["executed"] is False
    assert record["classification"] == "confirm"
    assert "denied" in record["reason"]
    assert record["result"] is None
    assert record["decided_by"] == "alice"


def test_the_diff_shows_added_and_removed_lines():
    """The approver sees the consequence: what leaves and what arrives."""
    diff = solution.render_diff(
        "alpha\nbeta\ngamma\n", "alpha\nBETA\ngamma\n", "notes.txt"
    )
    assert "-beta" in diff
    assert "+BETA" in diff


def test_a_write_confirmation_shows_the_diff_to_the_approver():
    """approve() must present the unified diff, not only the tool name."""
    prompts: list[str] = []

    def capture(prompt):
        prompts.append(prompt)
        return False

    solution.guarded_execute(
        {
            "name": "write_file",
            "arguments": {"path": "notes.txt", "content": "alpha\nBETA\ngamma\n"},
        },
        capture,
    )
    assert prompts, "confirm actions must call the approver"
    prompt = prompts[0]
    assert "-beta" in prompt
    assert "+BETA" in prompt
    assert "notes.txt" in prompt


def test_an_email_confirmation_shows_recipient_and_subject():
    """An irreversible send must surface to/subject as the consequence."""
    prompts: list[str] = []

    def capture(prompt):
        prompts.append(prompt)
        return False

    solution.guarded_execute(
        {
            "name": "send_email",
            "arguments": {
                "to": "team@example.com",
                "subject": "Weekly report",
                "body": "Status update.",
            },
        },
        capture,
    )
    assert prompts
    prompt = prompts[0]
    assert "team@example.com" in prompt
    assert "Weekly report" in prompt
    assert "to:" in prompt
    assert "subject:" in prompt


def test_every_path_returns_an_audit_record():
    """Refusal, auto, approval, and denial all name classification and actor."""

    def approve(prompt):
        return True

    def deny(prompt):
        return False

    records = [
        solution.guarded_execute(
            {"name": "delete_database", "arguments": {}}, approve
        ),
        solution.guarded_execute({"name": "list_files", "arguments": {}}, deny),
        solution.guarded_execute(
            {"name": "send_email", "arguments": {"to": "a@example.com"}},
            approve,
            actor="bob",
        ),
        solution.guarded_execute(
            {"name": "send_email", "arguments": {"to": "a@example.com"}},
            deny,
            actor="bob",
        ),
    ]
    classifications = [record["classification"] for record in records]
    assert classifications == ["forbidden", "auto", "confirm", "confirm"]
    assert [record["decided_by"] for record in records] == [
        "policy",
        "policy",
        "bob",
        "bob",
    ]
    for record in records:
        assert set(record) >= {
            "executed",
            "classification",
            "reason",
            "result",
            "decided_by",
        }
        assert record["reason"]


def test_a_refusal_comes_back_as_a_tool_result_with_the_reason():
    """Step 6: a denied action is information for the model, not a dead end."""

    def deny(prompt):
        return False

    record = solution.guarded_execute(
        {
            "name": "send_email",
            "arguments": {"to": "team@example.com", "subject": "Weekly report"},
        },
        deny,
    )
    block = solution.as_tool_result(record, "toolu_1")
    assert block["type"] == "tool_result"
    assert block["tool_use_id"] == "toolu_1"
    assert block["is_error"] is True
    assert "confirm" in block["content"]
    assert "denied" in block["content"]


def test_a_successful_action_comes_back_as_a_non_error_tool_result():
    """Executed actions still use as_tool_result so the wiring stays one path."""
    record = solution.guarded_execute(
        {"name": "list_files", "arguments": {}},
        lambda prompt: False,
    )
    block = solution.as_tool_result(record, "toolu_2")
    assert block["is_error"] is False
    assert block["content"] == record["result"]
    assert "notes.txt" in block["content"]
