"""Tests for Lab 01 - The augmented LLM.

Retrieval, memory, and tool dispatch are deterministic and are tested offline.
Only the end-to-end call needs an API key, and it skips without one.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

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
solution = _load("lab01_solution", LAB_ROOT / "solution" / "main.py")

requires_api = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY")
    or importlib.util.find_spec("anthropic") is None,
    reason="needs ANTHROPIC_API_KEY and the anthropic package",
)


def test_tokenize_is_lowercase_and_word_only():
    """Tokenization ignores case and punctuation."""
    assert solution.tokenize("Refunds, within 30 DAYS.") == {
        "refunds",
        "within",
        "30",
        "days",
    }


def test_retrieve_ranks_the_relevant_document_first():
    """The document sharing the most query tokens wins."""
    hits = solution.retrieve("how long is the warranty", solution.CORPUS, k=1)
    assert [doc.id for doc in hits] == ["warranty-policy"]


def test_retrieve_drops_documents_with_no_overlap():
    """Irrelevant documents are not padded in to reach k."""
    hits = solution.retrieve("zzzz", solution.CORPUS, k=3)
    assert hits == []


def test_retrieve_respects_k():
    """At most k documents come back."""
    hits = solution.retrieve("shipping returns warranty business", solution.CORPUS, k=2)
    assert len(hits) == 2


def test_build_system_includes_every_retrieved_document_id():
    """Retrieved text is labelled so answers can cite it."""
    context = solution.retrieve("returns", solution.CORPUS, k=1)
    system = solution.build_system(context)
    assert "[returns-policy]" in system
    assert "30 days" in system


def test_build_system_handles_an_empty_context():
    """No match is stated plainly rather than silently omitted."""
    assert "no documents matched" in solution.build_system([])


def test_memory_keeps_only_the_most_recent_turns():
    """Memory is a fixed budget: the oldest turns fall off."""
    memory = solution.Memory(max_turns=2)
    memory.add("user", "one")
    memory.add("assistant", "two")
    memory.add("user", "three")
    assert [turn["content"] for turn in memory.turns] == ["two", "three"]


def test_memory_messages_returns_a_copy():
    """Callers cannot mutate memory by editing the messages list."""
    memory = solution.Memory()
    memory.add("user", "hello")
    messages = memory.messages()
    messages[0]["content"] = "changed"
    assert memory.turns[0]["content"] == "hello"


def test_run_tool_returns_live_state():
    """The tool reads state that the corpus does not contain."""
    output, is_error = solution.run_tool("get_stock_level", {"sku": "SKU-100"})
    assert is_error is False
    assert "12" in output


def test_run_tool_reports_an_unknown_sku_as_a_recoverable_error():
    """A bad input returns is_error plus the valid options, and does not raise."""
    output, is_error = solution.run_tool("get_stock_level", {"sku": "SKU-999"})
    assert is_error is True
    assert "SKU-100" in output


def test_run_tool_reports_an_unknown_tool_name():
    """An unknown tool is an error result, not an exception."""
    output, is_error = solution.run_tool("delete_everything", {})
    assert is_error is True
    assert "unknown tool" in output.lower()


@requires_api
def test_augmented_call_answers_from_the_retrieved_document():
    """A grounded question is answered from the corpus."""
    memory = solution.Memory()
    answer = solution.augmented_call(
        "How many days do I have to return an item?", memory=memory
    )
    assert "30" in answer
    assert len(memory.turns) == 2


@requires_api
def test_augmented_call_uses_the_tool_for_a_stock_question():
    """Stock is live state, so the model must reach for the tool."""
    answer = solution.augmented_call("How many units of SKU-300 are in stock?")
    assert "47" in answer
