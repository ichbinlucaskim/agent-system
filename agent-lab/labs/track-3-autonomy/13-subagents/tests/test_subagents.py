"""Tests for Lab 13 - Subagents.

Tool restriction, context isolation, concurrency, and the comparison
harness are driven through model_call and executor injection points with
scripted responses, so every test runs offline without an API key.
"""

from __future__ import annotations

import importlib.util
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


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
solution = _load("lab13_solution", LAB_ROOT / "solution" / "main.py")

SECRET_MARKER = "SECRET_NOTE_BODY_DO_NOT_LEAK_7f3a"


def _usage() -> SimpleNamespace:
    return SimpleNamespace(
        input_tokens=150,
        output_tokens=30,
        cache_read_input_tokens=0,
        cache_creation_input_tokens=0,
    )


def _text_response(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        stop_reason="end_turn",
        usage=_usage(),
    )


def _tool_then_text(tool_name: str, arguments: dict, text: str):
    """Yield a tool_use response, then a final text response."""
    yield SimpleNamespace(
        content=[
            SimpleNamespace(
                type="tool_use",
                id="toolu_0",
                name=tool_name,
                input=arguments,
            )
        ],
        stop_reason="tool_use",
        usage=_usage(),
    )
    yield _text_response(text)


def _spec(**overrides: Any) -> Any:
    values: dict[str, Any] = dict(
        name="returns-reader",
        system="You answer questions about returns only.",
        allowed_tools=["read_note"],
        task="Summarize the return policy.",
    )
    values.update(overrides)
    return solution.SubagentSpec(**values)


def test_restrict_tools_returns_only_the_allowed_tools():
    """A spec allowing one tool yields exactly that definition."""
    tools = solution.restrict_tools(solution.ALL_TOOLS, ["read_note"])
    assert [tool["name"] for tool in tools] == ["read_note"]


def test_restrict_tools_raises_on_a_tool_the_parent_lacks():
    """A typo fails loudly instead of quietly granting a shorter list."""
    with pytest.raises(ValueError, match="delete_everything"):
        solution.restrict_tools(solution.ALL_TOOLS, ["read_note", "delete_everything"])


def test_the_parent_has_a_write_tool_the_children_do_not():
    """Capability restriction is visible in the tool sets, not only in prose."""
    parent_names = {tool["name"] for tool in solution.ALL_TOOLS}
    assert "write_note" in parent_names
    for spec in solution._demo_specs():
        assert "write_note" not in spec.allowed_tools
        child_names = {
            tool["name"]
            for tool in solution.restrict_tools(solution.ALL_TOOLS, spec.allowed_tools)
        }
        assert "write_note" not in child_names
        assert child_names <= {"list_notes", "read_note"}


def test_a_subagent_starts_with_no_parent_history():
    """The child's first model call carries its own subtask and nothing else."""
    captured: list[list[dict]] = []

    def call(messages, tools, system):
        captured.append([dict(message) for message in messages])
        return _text_response("Returns close after 30 days.")

    spec = _spec(task="Summarize the return policy.")
    solution.run_subagent(spec, solution.ALL_TOOLS, model_call=call)
    assert captured[0] == [
        {"role": "user", "content": "Summarize the return policy."}
    ]


def test_a_subagent_runs_its_own_subtask_not_the_parent_task():
    """Fan-out means each child is asked its own question."""
    seen_tasks: list[str] = []

    def call(messages, tools, system):
        seen_tasks.append(messages[0]["content"])
        return _text_response("ok")

    specs = [
        _spec(name="a", task="Subtask A only."),
        _spec(name="b", task="Subtask B only."),
    ]
    solution.with_subagents(
        "Parent combined task.", specs, solution.ALL_TOOLS, model_call=call
    )
    assert "Subtask A only." in seen_tasks
    assert "Subtask B only." in seen_tasks
    # Children must not be handed the parent's combined question as their task.
    assert "Subtask A only." != "Parent combined task."
    parent_calls = [text for text in seen_tasks if text.startswith("Task:")]
    assert len(parent_calls) == 1
    assert "Parent combined task." in parent_calls[0]


def test_a_subagent_cannot_call_a_tool_outside_its_spec():
    """A tool_use naming a restricted tool is refused, not executed."""
    executed: list[str] = []

    def executor(name, arguments):
        executed.append(name)
        return ("ok", False)

    responses = iter(
        [
            SimpleNamespace(
                content=[
                    SimpleNamespace(
                        type="tool_use",
                        id="toolu_0",
                        name="write_note",
                        input={"filename": "x.md", "body": "pwned"},
                    )
                ],
                stop_reason="tool_use",
                usage=_usage(),
            ),
            _text_response("Done."),
        ]
    )

    def call(messages, tools, system):
        return next(responses)

    spec = _spec(allowed_tools=["read_note"])
    result = solution.run_subagent(
        spec, solution.ALL_TOOLS, model_call=call, executor=executor
    )

    assert executed == []
    tool_results = [
        block
        for message in result["messages"]
        if isinstance(message.get("content"), list)
        for block in message["content"]
        if isinstance(block, dict) and block.get("type") == "tool_result"
    ]
    assert tool_results
    assert tool_results[0]["is_error"] is True
    assert "not available" in tool_results[0]["content"]


def test_the_parent_briefing_excludes_child_transcripts_and_note_bodies():
    """Context isolation: the parent sees reports, never what the child read."""
    parent_payloads: list[str] = []

    def executor(name, arguments):
        if name == "read_note":
            return (f"Body with {SECRET_MARKER} inside.", False)
        return ("ok", False)

    child_turns = {
        "returns-reader": iter(
            _tool_then_text(
                "read_note",
                {"filename": "returns.md"},
                "Returns close after 30 days.",
            )
        ),
        "shipping-reader": iter(
            _tool_then_text(
                "read_note",
                {"filename": "shipping.md"},
                "Express arrives next business day.",
            )
        ),
    }

    def call(messages, tools, system):
        blob = repr(messages)
        if not tools:
            parent_payloads.append(blob)
            return _text_response("Combined answer.")
        first = str(messages[0]["content"])
        if "return" in first.lower():
            return next(child_turns["returns-reader"])
        return next(child_turns["shipping-reader"])

    specs = [
        _spec(
            name="returns-reader",
            task="What is the return window?",
            allowed_tools=["read_note"],
        ),
        _spec(
            name="shipping-reader",
            task="How fast is express shipping?",
            allowed_tools=["read_note"],
        ),
    ]
    result = solution.with_subagents(
        "Combined parent task.",
        specs,
        solution.ALL_TOOLS,
        model_call=call,
        executor=executor,
    )

    assert parent_payloads, "parent model_call was never invoked"
    parent_blob = parent_payloads[0]
    assert SECRET_MARKER not in parent_blob
    assert "role': 'assistant'" not in parent_blob
    assert "Returns close after 30 days." in parent_blob
    assert "Express arrives next business day." in parent_blob
    assert SECRET_MARKER not in result["briefing"]
    assert SECRET_MARKER not in result["answer"]


def test_subagents_run_concurrently():
    """Fan-out overlaps on the wall clock; a serial loop would take longer."""
    lock = threading.Lock()
    active = {"n": 0, "peak": 0}

    def call(messages, tools, system):
        if tools:
            with lock:
                active["n"] += 1
                active["peak"] = max(active["peak"], active["n"])
            time.sleep(0.15)
            with lock:
                active["n"] -= 1
            return _text_response("child report")
        return _text_response("parent answer")

    specs = [
        _spec(name="a", task="Subtask A."),
        _spec(name="b", task="Subtask B."),
    ]
    started = time.perf_counter()
    result = solution.with_subagents(
        "Parent task.", specs, solution.ALL_TOOLS, model_call=call
    )
    elapsed = time.perf_counter() - started

    assert active["peak"] >= 2
    assert elapsed < 0.28
    assert result["seconds"] < 0.28


def test_compare_reports_totals_for_both_approaches():
    """Both runs come back with token totals, steps, and measured time."""

    def call(messages, tools, system):
        time.sleep(0.01)
        return _text_response("The return window is 30 days.")

    spec = _spec(task="What is the return window?")
    result = solution.compare(
        "What is the return window?", [spec], solution.ALL_TOOLS, model_call=call
    )
    for label in ("single", "subagents"):
        run = result[label]
        assert run["total_tokens"] > 0
        assert run["steps"] >= 1
        assert run["seconds"] > 0.0
        assert run["answer"]


def test_a_child_run_names_its_stop_reason():
    """Lab-12-shaped loops report why they stopped."""

    def call(messages, tools, system):
        return _text_response("Done.")

    result = solution.run_subagent(_spec(), solution.ALL_TOOLS, model_call=call)
    assert result["stop_reason"] == "completed"
