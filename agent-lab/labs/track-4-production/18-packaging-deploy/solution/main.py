"""Lab 18 - Packaging and deployment (reference solution).

Two thin entry points, one core function. Configuration comes from the
environment and is validated at startup, the health check never touches the
model, and a smoke test proves the process starts and answers.

Environment variables:
    ANTHROPIC_API_KEY           required; load_config and the CLI refuse to start without it
    LAB_MODEL                   optional; model id, defaults to the lab default
    AGENT_PORT                  optional; HTTP port, defaults to 8080
    AGENT_MAX_QUESTION_CHARS    optional; input length cap, defaults to 2000
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass, replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from common.client import DEFAULT_MODEL, complete, text_of


class ConfigError(RuntimeError):
    """Raised at startup when the environment is missing or malformed."""


@dataclass(frozen=True)
class Config:
    """Every setting the process needs, read from the environment.

    Defaults live here and nowhere else, so there is exactly one place to
    look when asking what a deployment will do.
    """

    api_key: str
    model: str = DEFAULT_MODEL
    port: int = 8080
    max_question_chars: int = 2_000


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc


def load_config() -> Any:
    """Read and validate configuration at startup.

    A missing variable is reported by name, immediately. Failing at startup
    beats failing on the first request an hour later.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise ConfigError(
            "missing required environment variable ANTHROPIC_API_KEY; "
            "copy .env.example to .env and export it before starting"
        )
    return Config(
        api_key=api_key,
        model=os.environ.get("LAB_MODEL", "").strip() or DEFAULT_MODEL,
        port=_int_env("AGENT_PORT", 8080),
        max_question_chars=_int_env("AGENT_MAX_QUESTION_CHARS", 2_000),
    )


def answer(question: str, config: Any) -> dict[str, Any]:
    """The single core function both entry points call.

    The CLI and the HTTP handler are both thin adapters over this. When each
    entry point carries its own logic, they drift and the same bug ships
    twice.
    """
    question = question.strip()
    if not question:
        raise ValueError("question is empty")
    if len(question) > config.max_question_chars:
        raise ValueError(
            f"question is {len(question)} characters, the limit is "
            f"{config.max_question_chars}"
        )
    response = complete(
        [{"role": "user", "content": question}], model=config.model
    )
    return {"question": question, "answer": text_of(response), "model": config.model}


def build_parser() -> Any:
    """Build the argparse parser for the CLI.

    Every option has a default and a help string; the parser is the CLI's
    documentation.
    """
    parser = argparse.ArgumentParser(
        prog="agent",
        description="Ask the agent one question and print the JSON result.",
    )
    parser.add_argument("question", help="the question to send to the agent")
    parser.add_argument(
        "--model",
        default=None,
        help=f"model id override (default: LAB_MODEL or {DEFAULT_MODEL})",
    )
    return parser


def run_cli(argv: list[str] | None = None) -> int:
    """Parse arguments, call the core, print the result, return an exit code.

    Non-zero on failure, so a shell script can branch on it. Printing an
    error and returning 0 makes failures invisible to automation.
    """
    args = build_parser().parse_args(argv)
    try:
        config = load_config()
    except ConfigError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2
    if args.model:
        config = replace(config, model=args.model)
    try:
        result = answer(args.question, config)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


class AgentServer(ThreadingHTTPServer):
    """Carries the config and the core function for its handlers.

    Injecting the core here lets the smoke test run the full HTTP path with
    a stub core when no API key is available.
    """

    def __init__(
        self,
        config: Config,
        core: Callable[[str, Config], dict[str, Any]] = answer,
        port: int = 0,
    ) -> None:
        super().__init__(("127.0.0.1", port), AgentHandler)
        self.config = config
        self.core = core


class AgentHandler(BaseHTTPRequestHandler):
    """A thin HTTP adapter over the same core function.

    http.server is not a production server and does not pretend to be one;
    it exists to show the shape. Swapping in a real server later changes
    this adapter, not the agent.
    """

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - fixed by BaseHTTPRequestHandler
        if self.path != "/health":
            self._send_json(404, {"error": f"unknown path {self.path}"})
            return
        # Deliberately no model call: this reports that the process is up and
        # configured, not that the provider is. A probe that costs a model
        # call per hit measures the wrong thing and bills for it.
        self._send_json(200, {"status": "ok", "model": self.server.config.model})

    def do_POST(self) -> None:  # noqa: N802 - fixed by BaseHTTPRequestHandler
        if self.path != "/answer":
            self._send_json(404, {"error": f"unknown path {self.path}"})
            return
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw)
            question = payload["question"]
            if not isinstance(question, str):
                raise TypeError("question must be a string")
        except (json.JSONDecodeError, KeyError, TypeError, UnicodeDecodeError):
            # Malformed input is the caller's error: a clean 400, never a
            # traceback.
            self._send_json(
                400, {"error": "body must be JSON with a string 'question' field"}
            )
            return
        try:
            result = self.server.core(question, self.server.config)
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
            return
        self._send_json(200, result)

    def log_message(self, format: str, *args: Any) -> None:
        # Keep per-request logging out of test and smoke test output.
        return


def _echo_core(question: str, config: Config) -> dict[str, Any]:
    """A stand-in core for keyless smoke tests. Proves plumbing, not quality."""
    return {"question": question, "answer": f"echo: {question}", "model": config.model}


def smoke_test(port: int = 0) -> bool:
    """Start the server, probe it, and report one pass or fail.

    Three probes: health, one malformed request, one valid request. This
    proves the thing starts and answers; lab 15 is what proves it is any
    good, and confusing the two leaves a green pipeline in front of a wrong
    agent. Any probe error is a failed smoke, not an uncaught exception.
    """
    try:
        config, core = load_config(), answer
    except ConfigError:
        # No key in the environment: exercise the full HTTP path with an
        # echo core instead of touching the model. Real deployments still
        # refuse via load_config / run_cli; this path is for offline plumbing.
        config, core = Config(api_key=""), _echo_core

    server = AgentServer(config, core=core, port=port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    checks: list[bool] = []
    try:
        try:
            with urllib.request.urlopen(f"{base}/health", timeout=5) as response:
                checks.append(response.status == 200)
        except urllib.error.HTTPError as exc:
            checks.append(exc.code == 200)
        except OSError:
            checks.append(False)

        malformed = urllib.request.Request(
            f"{base}/answer", data=b"not json", method="POST"
        )
        try:
            urllib.request.urlopen(malformed, timeout=5)
            checks.append(False)
        except urllib.error.HTTPError as exc:
            checks.append(exc.code == 400)
        except OSError:
            checks.append(False)

        valid = urllib.request.Request(
            f"{base}/answer",
            data=json.dumps({"question": "Is the service alive?"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(valid, timeout=30) as response:
                body = json.loads(response.read())
                checks.append(response.status == 200 and "answer" in body)
        except (urllib.error.HTTPError, OSError, json.JSONDecodeError):
            checks.append(False)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    return bool(checks) and all(checks)


def main() -> int:
    """Validate the configuration, run the smoke test, and report."""
    try:
        config = load_config()
        print(f"config loaded: model={config.model} port={config.port}")
    except ConfigError as exc:
        print(f"config: {exc}")
        print("running the smoke test with an echo core instead")

    passed = smoke_test()
    print(f"smoke test {'passed' if passed else 'failed'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
