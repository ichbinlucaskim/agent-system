"""Environment configuration for the answer engine (lab 18 shape).

Purpose
    Validate settings at process start, not on the first failing request.

Why
    Missing keys and bad ports should fail loud at boot.

Trade-offs
    ``require_api_key=False`` lets smoke/offline run without a secret; live ask
    still requires the key via the CLI entrypoint.

Edges
    Empty env vars fall back to defaults. Malformed ints/floats raise ConfigError.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from common.client import DEFAULT_MODEL


class ConfigError(RuntimeError):
    """Raised when an environment variable is missing or malformed."""


@dataclass(frozen=True)
class Config:
    """Immutable process settings.

    Purpose
        Single place to read port, top_k, score floor, and model id.

    Why
        Frozen dataclass prevents silent mutation after startup validation.

    Trade-offs
        All knobs are env-driven; no config file.

    Edges
        ``api_key="offline"`` is a sentinel used when the key is optional.
    """

    api_key: str
    model: str = DEFAULT_MODEL
    port: int = 8080
    max_chars: int = 2_000
    top_k: int = 3
    min_score: float = 0.05


def _int_env(name: str, default: int) -> int:
    """Parse an optional integer env var.

    Purpose / Why / Trade-offs / Edges
        Shared helper so ConfigError messages name the variable. Empty → default.
        Non-integer → ConfigError.
    """
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc


def _float_env(name: str, default: float) -> float:
    """Parse an optional float env var. Same contract as ``_int_env``."""
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number, got {raw!r}") from exc


def load_config(*, require_api_key: bool = True) -> Config:
    """Read and validate configuration from the environment.

    Purpose
        Startup gate for CLI/HTTP.

    Why
        Fail before binding a port when the key is required but missing.

    Trade-offs
        Does not check that the API key is *valid*, only that it is present.

    Edges
        When require_api_key is False and the key is absent, api_key becomes
        the string ``offline``.
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
        port=_int_env("ANSWER_ENGINE_PORT", 8080),
        max_chars=_int_env("ANSWER_ENGINE_MAX_CHARS", 2_000),
        top_k=_int_env("ANSWER_ENGINE_TOP_K", 3),
        min_score=_float_env("ANSWER_ENGINE_MIN_SCORE", 0.05),
    )
