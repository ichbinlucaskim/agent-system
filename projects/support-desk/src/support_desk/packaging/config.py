"""Startup configuration from the environment (lab 18 shape).

Purpose
    Parse and validate process env into a frozen ``Config`` (API key, model,
    port, input/budget limits, optional DB path) or raise ``ConfigError``.

Why
    Packaging layer owns env mapping so agent code receives a typed object.
    Fail-fast at startup beats mid-request missing-key crashes.

Trade-offs
    ``require_api_key=False`` invents ``api_key="offline"`` for tests—never use
    that for live asks. Integer/float env parsers reject non-numeric strings
    with ``ConfigError``.

Edges
    Empty optional env vars fall back to defaults. Blank ``LAB_MODEL`` uses
    ``DEFAULT_MODEL`` from ``common.client``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from common.client import DEFAULT_MODEL


class ConfigError(RuntimeError):
    """Raised at startup when the environment is missing or malformed.

    Purpose
        Signal configuration failures distinctly from runtime agent errors.

    Why
        CLI/HTTP can map this to exit code 2 / stderr without treating it as a
        model failure.

    Trade-offs
        Subclasses ``RuntimeError`` for broad catch compatibility.

    Edges
        Message should name the variable and expected shape.
    """


@dataclass(frozen=True)
class Config:
    """Immutable runtime settings for one support-desk process.

    Purpose
        Carry API key, model, HTTP port, guardrail/budget limits, and DB path.

    Why
        Frozen dataclass prevents accidental mutation after load and documents
        the packaging contract for agent and adapters.

    Trade-offs
        ``db_path`` empty means callers create a temp DB. Defaults are lab-
        sized, not production SLOs.

    Edges
        ``api_key`` may be the sentinel ``offline`` when key requirement is
        waived.
    """

    api_key: str
    model: str = DEFAULT_MODEL
    port: int = 8080
    max_chars: int = 2_000
    max_steps: int = 8
    max_usd: float = 1.0
    db_path: str = ""


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number, got {raw!r}") from exc


def load_config(*, require_api_key: bool = True) -> Config:
    """Read and validate configuration from the process environment.

    Purpose
        Build a ``Config`` from env vars, optionally requiring an API key.

    Why
        Offline tests and some CLIs pass ``require_api_key=False`` so
        deterministic paths can run without a key. Live ask/serve keep the
        default True.

    Trade-offs
        Does not load ``.env`` files itself—operators must export vars (or use
        an external dotenv tool).

    Edges
        Missing key with require True → ``ConfigError``. Malformed ints/floats
        → ``ConfigError``.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if require_api_key and not api_key:
        raise ConfigError(
            "missing required environment variable ANTHROPIC_API_KEY; "
            "copy .env.example to .env and export it before starting"
        )
    return Config(
        api_key=api_key or "offline",
        model=os.environ.get("LAB_MODEL", "").strip() or DEFAULT_MODEL,
        port=_int_env("SUPPORT_DESK_PORT", 8080),
        max_chars=_int_env("SUPPORT_DESK_MAX_CHARS", 2_000),
        max_steps=_int_env("SUPPORT_DESK_MAX_STEPS", 8),
        max_usd=_float_env("SUPPORT_DESK_MAX_USD", 1.0),
        db_path=os.environ.get("SUPPORT_DESK_DB", "").strip(),
    )
