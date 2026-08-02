"""Tests for Lab 00 - Setup.

Tests that need a live API call skip cleanly when ANTHROPIC_API_KEY is absent.
Everything else runs offline.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def _load(name: str, path: Path):
    """Load a module by file path.

    Lab directories start with digits, so they cannot be imported as packages.
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
solution = _load("lab00_solution", LAB_ROOT / "solution" / "main.py")

requires_api = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY")
    or importlib.util.find_spec("anthropic") is None,
    reason="needs ANTHROPIC_API_KEY and the anthropic package",
)


def test_read_api_key_raises_a_clear_error_when_missing(monkeypatch):
    """A missing credential fails immediately with a named error type."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from common.client import MissingAPIKeyError, read_api_key

    with pytest.raises(MissingAPIKeyError) as excinfo:
        read_api_key()
    assert "ANTHROPIC_API_KEY" in str(excinfo.value)


def test_read_api_key_treats_whitespace_as_missing(monkeypatch):
    """An empty or whitespace value is not a usable key."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "   ")
    from common.client import MissingAPIKeyError, read_api_key

    with pytest.raises(MissingAPIKeyError):
        read_api_key()


def test_check_api_key_returns_a_masked_key(monkeypatch):
    """The key is never returned in full, but is still recognisable."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-abcdefghijklmnop9999")
    masked = solution.check_api_key()
    assert "abcdefghijklmnop" not in masked
    assert masked.startswith("sk-ant-")
    assert masked.endswith("9999")


def test_mask_reveals_nothing_for_short_keys():
    """A short key has no safe prefix, so nothing is shown."""
    assert set(solution.mask("short")) == {"."}


def test_usage_summary_reads_every_field():
    """Usage is read defensively and totalled."""
    response = SimpleNamespace(
        usage=SimpleNamespace(
            input_tokens=100,
            output_tokens=25,
            cache_read_input_tokens=10,
            cache_creation_input_tokens=5,
        )
    )
    summary = solution.usage_summary(response)
    assert summary["input_tokens"] == 100
    assert summary["output_tokens"] == 25
    assert summary["cache_read_tokens"] == 10
    assert summary["cache_creation_tokens"] == 5
    assert summary["total_tokens"] == 140


def test_usage_summary_defaults_missing_fields_to_zero():
    """A response without usage yields zeros rather than raising."""
    summary = solution.usage_summary(SimpleNamespace())
    assert summary["total_tokens"] == 0


@requires_api
def test_ask_returns_text_and_usage():
    """A non-streaming call returns text and reports non-zero token usage."""
    from common.client import text_of

    response = solution.ask("Reply with exactly the word: ready")
    assert text_of(response).strip()
    assert solution.usage_summary(response)["output_tokens"] > 0


@requires_api
def test_streaming_returns_the_same_kind_of_answer():
    """Streaming changes when text arrives, not whether text arrives."""
    text = solution.ask_streaming("Reply with exactly the word: ready")
    assert text.strip()
