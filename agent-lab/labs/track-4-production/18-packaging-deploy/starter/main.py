"""Lab 18 - Packaging and deployment (starter).

Goal: Wrap an agent as both a CLI and a thin HTTP handler using only the
standard library, drive its configuration entirely through the environment,
and prove it starts and answers with a smoke test.

Environment variables:
    ANTHROPIC_API_KEY           required; load_config / CLI refuse to start without it
    LAB_MODEL                   optional; model id, defaults to the lab default
    AGENT_PORT                  optional; HTTP port, defaults to 8080
    AGENT_MAX_QUESTION_CHARS    optional; input length cap, defaults to 2000

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-4-production/18-packaging-deploy/tests -v
"""

from __future__ import annotations

from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler
from typing import Any, Callable


class ConfigError(RuntimeError):
    """Raised at startup when the environment is missing or malformed."""


@dataclass(frozen=True)
class Config:
    """Every setting the process needs, read from the environment."""

    # TODO: step 1. api_key, model, port, max_question_chars. Defaults live
    # here so there is exactly one place to look.
    api_key: str = ""
    model: str = ""
    port: int = 8080
    max_question_chars: int = 2_000


def load_config() -> Any:
    """Read and validate configuration at startup."""
    # TODO: step 1. Raise ConfigError naming any missing/malformed variable
    # (ANTHROPIC_API_KEY, AGENT_PORT, …). Failing at startup beats failing on
    # the first request an hour later.
    raise NotImplementedError


def answer(question: str, config: Any) -> dict[str, Any]:
    """The single core function both entry points call."""
    # TODO: step 2. Validate the question, call the model, return a structured
    # dict. CLI and HTTP are thin adapters over this.
    raise NotImplementedError


def build_parser() -> Any:
    """Build the argparse parser for the CLI."""
    # TODO: step 3. Every option gets a default and a help string.
    raise NotImplementedError


def run_cli(argv: list[str] | None = None) -> int:
    """Parse arguments, call the core, print the result, return an exit code."""
    # TODO: step 3. ConfigError → exit 2; other failures → exit 1; success → 0.
    raise NotImplementedError


class AgentServer:
    """Carries config and the core function for its handlers."""

    # TODO: step 4. Subclass ThreadingHTTPServer (or similar). Default core
    # must be answer so CLI and HTTP cannot drift.


class AgentHandler(BaseHTTPRequestHandler):
    """A thin HTTP adapter over the same core function."""

    # TODO: step 4. GET /health → 200, never call the model.
    # POST /answer → 400 on malformed JSON or missing 'question'; 200 with
    # JSON body otherwise. http.server is the shape, not production.


def smoke_test(port: int = 0) -> bool:
    """Start the server, probe it, and report one pass or fail."""
    # TODO: step 5. Hit /health, one malformed POST, one valid POST. If
    # load_config fails, use an echo core so plumbing can still be proven
    # without a key — that is not a substitute for refusing to start the
    # real process.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Try load_config, run smoke_test, print pass/fail.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
