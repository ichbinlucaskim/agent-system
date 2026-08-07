"""CLI and HTTP adapters over handle_message (lab 18).

Purpose
    Provide process entrypoints: build ToolContext, argparse ``ask`` / ``serve``
    / ``smoke``, and a small Threading HTTP API with ``/health`` and ``/ask``.

Why
    Packaging adapters must stay thin. All customer handling delegates to
    ``agent.loop.handle_message`` so CLI and HTTP cannot diverge on guardrails,
    routing, or HITL wiring.

Trade-offs
    Shared in-memory/temp DB per process for serve—fine for demos, not multi-
    tenant isolation. HTTP ``approve`` defaults True from JSON. Interactive
    CLI approver blocks on stdin.

Edges
    ``ask``/``serve`` require API key; ``smoke`` does not. Smoke probes health
    only—no model call. Input guardrail on ask exits 2.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from support_desk.agent.loop import handle_message
from support_desk.packaging.config import Config, ConfigError, load_config
from support_desk.tools_gate.db import init_db
from support_desk.evaluation.observe import render_run_report
from support_desk.tools_gate.retrieve import build_policy_store
from support_desk.tools_gate.tools import ToolContext


def build_context(config: Config, *, db_path: str | Path | None = None) -> ToolContext:
    """Create a seeded DB connection and policy store for one process.

    Purpose
        Return a ``ToolContext`` ready for ``handle_message``.

    Why
        CLI, HTTP, and smoke share the same wiring so demos stay consistent.

    Trade-offs
        ``init_db`` wipes the target path—pass a temp path for disposable runs.
        Missing ``db_path`` and empty config path → anonymous temp file.

    Edges
        Explicit ``db_path`` overrides ``config.db_path``.
    """
    path = db_path or config.db_path
    if not path:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        path = tmp.name
        tmp.close()
    connection = init_db(path)
    return ToolContext(connection, build_policy_store())


def build_parser() -> argparse.ArgumentParser:
    """Construct the support-desk CLI argument parser.

    Purpose
        Define ``ask``, ``serve``, and ``smoke`` subcommands and flags.

    Why
        Keeps ``main`` thin and makes parser testable in isolation.

    Trade-offs
        ``command`` is required—no default subcommand.

    Edges
        Ask supports ``--approve`` / ``--deny`` / ``--report``. Smoke accepts
        ``--port`` (0 = ephemeral).
    """
    parser = argparse.ArgumentParser(prog="support-desk")
    sub = parser.add_subparsers(dest="command", required=True)

    ask = sub.add_parser("ask", help="Handle one customer message")
    ask.add_argument("message")
    ask.add_argument("--approve", action="store_true", help="Auto-approve confirm tools")
    ask.add_argument("--deny", action="store_true", help="Deny confirm tools")
    ask.add_argument("--report", action="store_true")

    sub.add_parser("serve", help="HTTP server with /health and /ask")
    smoke = sub.add_parser("smoke", help="Start briefly and probe /health")
    smoke.add_argument("--port", type=int, default=0)
    return parser


def _approver_from_args(args: argparse.Namespace) -> Callable[[str], bool]:
    if getattr(args, "deny", False):
        return lambda prompt: False
    if getattr(args, "approve", False):
        return lambda prompt: True

    def interactive(prompt: str) -> bool:
        print(prompt)
        answer = input("approve? [y/N] ").strip().lower()
        return answer in {"y", "yes"}

    return interactive


def cmd_ask(args: argparse.Namespace, config: Config) -> int:
    """Handle one CLI customer message and print JSON (optional report).

    Purpose
        Build context, call ``handle_message``, print the result, optionally
        print a run report.

    Why
        Primary interactive demo path for the packaging layer.

    Trade-offs
        Trace object is stripped from JSON (not easily serializable). Exit 2
        on input guardrail so scripts can distinguish refusal.

    Edges
        Approver comes from ``--approve`` / ``--deny`` / interactive stdin.
    """
    ctx = build_context(config)
    result = handle_message(
        args.message,
        ctx,
        config,
        approver=_approver_from_args(args),
    )
    print(json.dumps({k: v for k, v in result.items() if k != "trace"}, default=str, indent=2))
    if args.report:
        print(render_run_report(result, model=config.model))
    return 0 if result.get("stop_reason") != "input_guardrail" else 2


def make_handler(config: Config, ctx: ToolContext) -> type[BaseHTTPRequestHandler]:
    """Build an HTTP handler class closed over config and shared context.

    Purpose
        Serve ``GET /health`` and ``POST /ask`` without a heavy framework.

    Why
        Lab-scale packaging: stdlib HTTP is enough to prove the adapter shape.

    Trade-offs
        Access log is silenced. Shared ``ctx`` across threads—SQLite + call log
        are not hardened for heavy concurrency.

    Edges
        Unknown paths → 404. Invalid JSON on ask → 400. Approve defaults from
        JSON body ``approve`` (default True).
    """

    class Handler(BaseHTTPRequestHandler):
        """Minimal health and ask endpoints for support-desk.

        Purpose
            Implement GET/POST routing for the demo server.

        Why
            Nested class captures ``config`` and ``ctx`` without globals.

        Trade-offs
            No auth, CORS, or request size caps beyond Content-Length trust.

        Edges
            ``log_message`` is a no-op to keep smoke output clean.
        """

        def log_message(self, format: str, *args: Any) -> None:
            """Suppress default BaseHTTPRequestHandler access logs.

            Purpose
                Keep smoke and demo stdout free of per-request noise.

            Why
                Stdlib logging would drown the health/ask payloads operators care
                about in this lab.

            Trade-offs
                Hides useful production access logs; re-enable for real deploys.

            Edges
                Format and args are ignored entirely.
            """
            return

        def do_GET(self) -> None:
            """Serve health JSON or 404.

            Purpose
                Answer liveness probes for smoke and orchestration.

            Why
                Smoke must not need a model call.

            Trade-offs
                Only exact ``/health`` (trailing slash stripped).

            Edges
                Other GET paths → 404.
            """
            if self.path.rstrip("/") == "/health":
                body = json.dumps({"ok": True, "service": "support-desk"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_error(404)

        def do_POST(self) -> None:
            """Handle ``/ask`` JSON bodies via ``handle_message``.

            Purpose
                Accept ``{message, approve?}`` and return the agent result JSON.

            Why
                HTTP adapter should mirror CLI ask without duplicating loop code.

            Trade-offs
                Trace omitted from response. Approve defaults True when omitted.

            Edges
                Non-``/ask`` → 404. Bad JSON → 400.
            """
            if self.path.rstrip("/") != "/ask":
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8"))
                message = str(payload.get("message", ""))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self.send_error(400, "invalid json")
                return
            result = handle_message(
                message,
                ctx,
                config,
                approver=lambda prompt: bool(payload.get("approve", True)),
            )
            body = json.dumps(
                {k: v for k, v in result.items() if k != "trace"},
                default=str,
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def cmd_serve(config: Config) -> int:
    """Run the HTTP server until KeyboardInterrupt.

    Purpose
        Bind ``127.0.0.1:config.port`` and serve forever.

    Why
        Long-running packaging demo for /health and /ask.

    Trade-offs
        Localhost only. Blocking ``serve_forever`` in the main thread.

    Edges
        Ctrl-C prints shutting down and closes the server. Always returns 0
        after clean shutdown.
    """
    ctx = build_context(config)
    server = ThreadingHTTPServer(("127.0.0.1", config.port), make_handler(config, ctx))
    print(f"support-desk listening on http://127.0.0.1:{config.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("shutting down")
    finally:
        server.server_close()
    return 0


def smoke_test(config: Config, *, port: int | None = None) -> int:
    """Prove the process starts and /health answers without a model call.

    Purpose
        Boot a short-lived server, GET health, shut down, return exit status.

    Why
        Packaging CI signal that imports, config (without key), and HTTP wiring
        work before spending on live asks.

    Trade-offs
        Does not exercise ``/ask``. Uses a daemon thread for serve_forever.

    Edges
        ``port`` None/0 → ephemeral bind. Failure prints to stderr and returns 1.
    """
    bind_port = port if port is not None else 0
    ctx = build_context(config)
    server = ThreadingHTTPServer(("127.0.0.1", bind_port), make_handler(config, ctx))
    chosen = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{chosen}/health", timeout=2) as resp:
            payload = json.loads(resp.read().decode())
        if not payload.get("ok"):
            print("smoke failed: health payload not ok", file=sys.stderr)
            return 1
        print(f"smoke ok on port {chosen}")
        return 0
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"smoke failed: {exc}", file=sys.stderr)
        return 1
    finally:
        server.shutdown()
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    """CLI entry: parse args, load config, dispatch ask/serve/smoke.

    Purpose
        Return a process exit code for ``python -m support_desk`` and console
        scripts.

    Why
        Single packaging main keeps key requirements and command routing in one
        place.

    Trade-offs
        Unknown command after parse falls through to return 1 (argparse usually
        prevents this).

    Edges
        ``ConfigError`` → stderr + exit 2. Ask/serve require API key; smoke
        does not.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        # smoke and unit paths can omit the key; ask/serve need it for live model.
        require = args.command in {"ask", "serve"}
        config = load_config(require_api_key=require)
        if args.command == "serve":
            return cmd_serve(config)
        if args.command == "smoke":
            return smoke_test(config, port=args.port or None)
        if args.command == "ask":
            return cmd_ask(args, config)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
