"""Lab 18 - Packaging and deployment (starter).

Goal: Wrap an agent as both a CLI and a thin HTTP handler using only the standard library, drive its configuration entirely through the environment, and prove it starts and answers with a smoke test.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-4-production/18-packaging-deploy/tests -v
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class Config:
    """Every setting the process needs, read from the environment."""

    # TODO: step 1. A dataclass with the model, the port, and any limits. Keep defaults here so there is exactly one place to look.


def load_config() -> Any:
    """Read and validate configuration at startup."""
    # TODO: step 1. Raise a clear error naming any missing required variable. Failing at startup beats failing on the first request an hour later.
    raise NotImplementedError


def answer(question: str, config: Any) -> dict[str, Any]:
    """The single core function both entry points call."""
    # TODO: step 2. Two thin adapters over one core. When the CLI and the handler each have their own logic, they drift and the same bug ships twice.
    raise NotImplementedError


def build_parser() -> Any:
    """Build the argparse parser for the CLI."""
    # TODO: step 3. Give every option a default and a help string. The parser is the CLI's documentation.
    raise NotImplementedError


def run_cli(argv: list[str] | None = None) -> int:
    """Parse arguments, call the core, print the result, return an exit code."""
    # TODO: step 3. Return non-zero on failure so a shell script can branch on it. Printing an error and returning 0 makes failures invisible to automation.
    raise NotImplementedError


class AgentHandler:
    """A thin HTTP adapter over the same core function."""

    # TODO: step 4. A BaseHTTPRequestHandler. /health must not call the model: it should report that this process is up and configured, not that the provider is. POST returns 400 on malformed JSON and 200 with a JSON body otherwise.


def smoke_test(port: int = 0) -> bool:
    """Start the server, probe it, and report one pass or fail."""
    # TODO: step 5. Health, one malformed request, one valid request. This proves the thing runs; lab 15 is what proves it is any good.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
