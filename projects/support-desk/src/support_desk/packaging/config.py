"""Startup configuration from the environment (lab 18 shape)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from common.client import DEFAULT_MODEL


class ConfigError(RuntimeError):
    """Raised at startup when the environment is missing or malformed."""


@dataclass(frozen=True)
class Config:
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
    """Read and validate configuration.

    Offline tests and some CLIs pass require_api_key=False so deterministic
    paths can run without a key.
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
