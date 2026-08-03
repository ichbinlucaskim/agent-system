"""Tests for Lab 18 - Packaging and deployment.

Configuration is driven through monkeypatched environment variables and the
HTTP path runs against an injected echo core, so every test runs offline and
passes whether or not ANTHROPIC_API_KEY is set in the surrounding shell.
"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Iterator

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
solution = _load("lab18_solution", LAB_ROOT / "solution" / "main.py")


@contextlib.contextmanager
def _serve(core: Callable[[str, Any], dict[str, Any]]) -> Iterator[str]:
    """Run an AgentServer with an injected core and yield its base URL.

    Port 0 lets the OS pick a free port, so tests never collide with a
    server the developer already has running.
    """
    server = solution.AgentServer(solution.Config(api_key=""), core=core, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_load_config_names_the_missing_variable(monkeypatch):
    """A missing required variable is reported by name at startup."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(solution.ConfigError, match="ANTHROPIC_API_KEY"):
        solution.load_config()


def test_load_config_applies_defaults(monkeypatch):
    """Optional settings fall back to documented defaults, never None."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    for name in ("LAB_MODEL", "AGENT_PORT", "AGENT_MAX_QUESTION_CHARS"):
        monkeypatch.delenv(name, raising=False)
    config = solution.load_config()
    assert config.model == solution.DEFAULT_MODEL
    assert config.port == 8080
    assert config.max_question_chars == 2_000


def test_health_returns_200_without_an_api_key(monkeypatch):
    """/health reports that the process is up and never calls the model."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def exploding_core(question: str, config: Any) -> dict[str, Any]:
        raise AssertionError("the health check must not reach the core")

    with _serve(exploding_core) as base:
        with urllib.request.urlopen(f"{base}/health", timeout=5) as response:
            assert response.status == 200
            body = json.loads(response.read())
    assert body["status"] == "ok"


def test_malformed_json_returns_400():
    """An invalid body is the caller's error: a clean 400, not a traceback."""
    with _serve(solution._echo_core) as base:
        request = urllib.request.Request(
            f"{base}/answer", data=b"not json", method="POST"
        )
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            urllib.request.urlopen(request, timeout=5)
        assert excinfo.value.code == 400
        body = json.loads(excinfo.value.read())
    assert "error" in body


def test_the_cli_returns_a_non_zero_exit_code_on_failure(monkeypatch):
    """run_cli returns non-zero when the core raises, so automation can branch."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def failing_core(question: str, config: Any) -> dict[str, Any]:
        raise RuntimeError("the model is unreachable")

    monkeypatch.setattr(solution, "answer", failing_core)
    assert solution.run_cli(["will fail"]) == 1


def test_both_entry_points_call_the_same_core(monkeypatch):
    """The CLI and the handler both reach answer, so the paths cannot drift."""
    core = solution.answer
    # The handler's default core is the module's answer function.
    server = solution.AgentServer(solution.Config(api_key="test-key"))
    try:
        assert server.core is core
    finally:
        server.server_close()

    # The CLI resolves the same module attribute at call time.
    calls: list[str] = []

    def recording_core(question: str, config: Any) -> dict[str, Any]:
        calls.append(question)
        return {"question": question, "answer": "stub", "model": config.model}

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(solution, "answer", recording_core)
    assert solution.run_cli(["cli question"]) == 0
    assert calls == ["cli question"]
