"""CLI and HTTP adapters over ``answer_question`` (lab 18 packaging).

Purpose
    Expose the same core through ask, serve, and smoke without duplicating
    retrieval or synthesis logic.

Why
    Health checks and smoke must not call the model. Live ask may. Keeping
    adapters thin prevents drift between entry points.

Trade-offs
    Stdlib ``http.server`` only—no FastAPI. Enough to teach packaging, not to
    deploy at scale.

Edges
    ``ask --offline`` skips API key requirement. Smoke binds port 0 when unset.
    Invalid JSON on POST /ask → 400.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from answer_engine.packaging.config import Config, ConfigError, load_config
from answer_engine.pipeline import answer_question
from answer_engine.retrieval import CorpusIndex


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI subcommand parser.

    Purpose
        Define ask / serve / smoke surfaces.

    Why
        Argparse keeps the teaching surface dependency-free.

    Trade-offs
        No shell completions or rich help themes.

    Edges
        ``command`` is required; missing subcommand exits via argparse.
    """
    parser = argparse.ArgumentParser(prog="answer-engine")
    sub = parser.add_subparsers(dest="command", required=True)
    ask = sub.add_parser("ask", help="Answer one question")
    ask.add_argument("question")
    ask.add_argument("--offline", action="store_true", help="No model call; stitch passages")
    ask.add_argument("--json", action="store_true")
    sub.add_parser("serve", help="HTTP /health and /ask")
    smoke = sub.add_parser("smoke", help="Probe /health without a model call")
    smoke.add_argument("--port", type=int, default=0)
    return parser


def cmd_ask(args: argparse.Namespace, config: Config, index: CorpusIndex) -> int:
    """Handle one CLI question.

    Purpose
        Print answer (and optional JSON) for a single query.

    Why
        Forces offline when no real API key is configured.

    Trade-offs
        Always exit 0 on successful pipeline run, even when abstaining.

    Edges
        Empty citations omit the citations line in text mode.
    """
    offline = bool(args.offline) or config.api_key == "offline"
    result = answer_question(
        args.question, index, config, offline=offline
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["answer"])
        if result["citations"]:
            print("citations:", ", ".join(result["citations"]))
    return 0


def make_handler(config: Config, index: CorpusIndex) -> type[BaseHTTPRequestHandler]:
    """Build an HTTP handler closed over config and corpus index.

    Purpose
        Serve /health (no model) and /ask (pipeline).

    Why
        Closure avoids global mutable server state.

    Trade-offs
        ThreadingHTTPServer is fine for smoke/demo, not for production load.

    Edges
        Unknown paths → 404. Access log suppressed to keep smoke output clean.
    """

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            return

        def do_GET(self) -> None:
            if self.path.rstrip("/") == "/health":
                body = json.dumps({"ok": True, "service": "answer-engine"}).encode()
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
                question = str(payload.get("question", ""))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self.send_error(400, "invalid json")
                return
            offline = bool(payload.get("offline", config.api_key == "offline"))
            result = answer_question(question, index, config, offline=offline)
            body = json.dumps(result).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def smoke_test(config: Config, index: CorpusIndex, *, port: int | None = None) -> int:
    """Start briefly and GET /health without calling the model.

    Purpose
        Prove the process binds and answers liveness.

    Why
        Separates "deployed" from "smart" (lab 18).

    Trade-offs
        Does not POST /ask; retrieval bugs won't fail smoke.

    Edges
        port 0 → ephemeral port. Failures return exit code 1.
    """
    bind = port if port is not None else 0
    server = ThreadingHTTPServer(("127.0.0.1", bind), make_handler(config, index))
    chosen = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{chosen}/health", timeout=2) as resp:
            payload = json.loads(resp.read().decode())
        if not payload.get("ok"):
            print("smoke failed: health not ok", file=sys.stderr)
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
    """Process entrypoint for ``python -m answer_engine``.

    Purpose
        Dispatch subcommands after config + index load.

    Why
        Central place for ConfigError → exit 2.

    Trade-offs
        Index is rebuilt on every process start (fine for small corpus).

    Edges
        serve() blocks until killed. Unknown command falls through to exit 1.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        require = args.command in {"ask", "serve"} and not (
            args.command == "ask" and getattr(args, "offline", False)
        )
        config = load_config(require_api_key=require)
        index = CorpusIndex.build()
        if args.command == "ask":
            return cmd_ask(args, config, index)
        if args.command == "serve":
            server = ThreadingHTTPServer(
                ("127.0.0.1", config.port), make_handler(config, index)
            )
            print(f"answer-engine on http://127.0.0.1:{config.port}")
            server.serve_forever()
            return 0
        if args.command == "smoke":
            return smoke_test(config, index, port=args.port or None)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
