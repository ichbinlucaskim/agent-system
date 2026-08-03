"""Tests for Lab 13 - Subagents.

Tool restriction, context isolation, and the comparison harness are all
driven through the model_call and executor injection points with scripted
responses, so every test runs offline without an API key.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

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


def test_restrict_tools_returns_only_the_allowed_tools():
    """A spec allowing one tool yields exactly that definition."""
    tools = solution.restrict_tools(solution.ALL_TOOLS, ["read_note"])
    assert [tool["name"] for tool in tools] == ["read_note"]


def test_restrict_tools_raises_on_a_tool_the_parent_lacks():
    """A typo fails loudly instead of quietly granting a shorter list."""
    with pytest.raises(ValueError, match="delete_everything"):
        solution.restrict_tools(solution.ALL_TOOLS, ["read_note", "delete_everything"])


def test_a_subagent_starts_with_no_parent_history():
    """The child's first model call carries the task and nothing else."""
    captured: list[list[dict]] = []

    def call(messages, tools, system):
        captured.append([dict(message) for message in messages])
        return _text_response("Returns close after 30 days.")

    spec = solution.SubagentSpec(
        name="returns-reader",
        system="You answer questions about returns only.",
        allowed_tools=["read_note"],
    )
    solution.run_subagent(
        spec, "Summarize the return policy.", solution.ALL_TOOLS, model_call=call
    )
    assert captured[0] == [
        {"role": "user", "content": "Summarize the return policy."}
    ]


def test_a_subagent_cannot_call_a_tool_outside_its_spec():
    """A tool_use naming a restricted tool is refused, not executed."""
    executed: list[str] = []

    def executor(name, arguments):
        executed.append(name)
        return ("ok", False)

    # First the model asks for a tool the spec does not allow; then it stops.
    responses = iter(
        [
            SimpleNamespace(
                content=[
                    SimpleNamespace(
                        type="tool_use", id="toolu_0", name="list_notes", input={}
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

    spec = solution.SubagentSpec(
        name="reader", system="Read notes.", allowed_tools=["read_note"]
    )
    result = solution.run_subagent(
        spec, "Summarize.", solution.ALL_TOOLS, model_call=call, executor=executor
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


def test_compare_reports_totals_for_both_approaches():
    """Both runs come back with token totals, steps, and elapsed time."""

    def call(messages, tools, system):
        return _text_response("The return window is 30 days.")

    spec = solution.SubagentSpec(
        name="returns-reader",
        system="You answer questions about returns only.",
        allowed_tools=["read_note"],
    )
    result = solution.compare(
        "What is the return window?", [spec], solution.ALL_TOOLS, model_call=call
    )
    for label in ("single", "subagents"):
        run = result[label]
        assert run["total_tokens"] > 0
        assert run["steps"] >= 1
        assert run["seconds"] >= 0.0
        assert run["answer"]
