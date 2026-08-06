"""Tests for Lab 07 - Tool design and the agent-computer interface.

The tool definitions, the error formatting, and the selection arithmetic are
deterministic and are tested offline; selection_rate is exercised with a
stubbed select_tool. Only a live description comparison would need a key, and
no test here makes one.
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
solution = _load("lab07_solution", LAB_ROOT / "solution" / "main.py")


def test_every_tool_definition_is_structurally_valid():
    """Each tool has a name, a description, and an object input_schema."""
    tools = (
        solution.GOOD_TOOL,
        solution.VAGUE_TOOL,
        solution.TRIGGER_ONLY_TOOL,
        solution.SCHEMA_ONLY_TOOL,
        solution.DOCS_TOOL,
    )
    for tool in tools:
        assert tool["name"]
        assert tool["description"]
        assert tool["input_schema"]["type"] == "object"
        assert isinstance(tool["input_schema"]["properties"], dict)


def test_the_variants_differ_in_exactly_one_field_each():
    """The two middle variants isolate the wording and the schema.

    Without them the good and vague definitions differ in several fields at
    once and no single change can be credited for the difference.
    """
    good, vague = solution.GOOD_TOOL, solution.VAGUE_TOOL
    trigger_only, schema_only = solution.TRIGGER_ONLY_TOOL, solution.SCHEMA_ONLY_TOOL

    assert trigger_only["description"] == good["description"]
    assert trigger_only["input_schema"] == vague["input_schema"]
    assert schema_only["description"] == vague["description"]
    assert schema_only["input_schema"] == good["input_schema"]
    # Every variant is the same tool, so selection differences cannot be
    # explained by the name.
    names = {tool["name"] for tool in (good, vague, trigger_only, schema_only)}
    assert names == {"get_stock_level"}


def test_the_cases_put_the_two_tools_in_competition():
    """Some cases belong to the docs tool, which is what creates a decision.

    A lone tool is selected for anything vaguely related to it, so a case
    set that only ever expects one tool cannot detect a bad description.
    """
    expected = {expectation for _, expectation in solution.CASES}
    assert "get_stock_level" in expected
    assert "search_product_docs" in expected
    assert None in expected


def test_the_good_description_states_a_trigger_condition():
    """The good description says when to call, not only what the tool does."""
    good = solution.GOOD_TOOL["description"].lower()
    vague = solution.VAGUE_TOOL["description"].lower()
    trigger_words = ("call this", "whenever", "when ")
    assert any(phrase in good for phrase in trigger_words)
    assert not any(phrase in vague for phrase in trigger_words)


def test_the_good_schema_constrains_its_inputs():
    """The good schema closes the input space; the vague one accepts anything."""
    good_schema = solution.GOOD_TOOL["input_schema"]
    vague_schema = solution.VAGUE_TOOL["input_schema"]
    good_constrained = (
        "enum" in good_schema["properties"]["sku"] or "required" in good_schema
    )
    assert good_constrained
    assert "enum" not in vague_schema["properties"]["sku"]
    assert "required" not in vague_schema


def test_format_tool_error_lists_the_valid_options():
    """The message names every valid option, so the model can fix its call."""
    message = solution.format_tool_error(
        "unknown SKU 'SKU-999'", ["SKU-100", "SKU-200", "SKU-300"]
    )
    for option in ("SKU-100", "SKU-200", "SKU-300"):
        assert option in message


def test_selection_rate_matches_a_hand_counted_example(monkeypatch):
    """Three matches out of four is 0.75, and no cases at all is 0.0."""
    cases: list[tuple[str, str | None]] = [
        ("q1", "get_stock_level"),
        ("q2", "get_stock_level"),
        ("q3", "get_stock_level"),
        ("q4", None),
    ]
    # The stub matches the expectation for every case except q4, where it
    # calls a tool although the correct behaviour is to call nothing.
    answers = {"q1": "get_stock_level", "q2": "get_stock_level",
               "q3": "get_stock_level", "q4": "get_stock_level"}
    monkeypatch.setattr(
        solution, "select_tool", lambda question, tools: answers[question]
    )
    assert solution.selection_rate(cases, [solution.GOOD_TOOL]) == 0.75
    assert solution.selection_rate([], [solution.GOOD_TOOL]) == 0.0


def test_compare_descriptions_varies_one_tool_against_a_fixed_competitor(monkeypatch):
    """Four rates come back, and every run sees the same docs tool."""
    seen: list[list[dict[str, object]]] = []

    def fake_select_tool(question: str, tools: list[dict[str, object]]):
        seen.append(tools)
        return "get_stock_level"

    monkeypatch.setattr(solution, "select_tool", fake_select_tool)
    rates = solution.compare_descriptions([("q1", "get_stock_level")])

    assert set(rates) == {"vague", "trigger_only", "schema_only", "good"}
    assert len(seen) == 4
    for tools in seen:
        assert [tool["name"] for tool in tools] == [
            "get_stock_level",
            "search_product_docs",
        ]
        assert tools[1] == solution.DOCS_TOOL
