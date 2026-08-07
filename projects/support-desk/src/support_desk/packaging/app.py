"""CLI and HTTP adapters over handle_message (lab 18)."""

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
    path = db_path or config.db_path
    if not path:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        path = tmp.name
        tmp.close()
    connection = init_db(path)
    return ToolContext(connection, build_policy_store())


def build_parser() -> argparse.ArgumentParser:
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
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            return

        def do_GET(self) -> None:
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
    """Prove the process starts and /health answers without a model call."""
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
