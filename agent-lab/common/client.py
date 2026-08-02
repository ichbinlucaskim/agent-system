"""Thin wrapper around the Anthropic SDK.

Every lab talks to the model through this module so that model selection,
credential handling, and error messages stay consistent across the repository.

The API key is read from the ANTHROPIC_API_KEY environment variable. Copy
.env.example to .env and export the variable before running any lab that makes
a real request.

The anthropic package is imported lazily inside get_client so that the rest of
this module can be imported (and unit tested) without the SDK installed.
"""

from __future__ import annotations

import os
from typing import Any, Iterator

# Default model for the labs. Override per call with the model keyword, or
# globally with the LAB_MODEL environment variable.
DEFAULT_MODEL = "claude-opus-5"

# Conservative defaults. max_tokens bounds thinking plus visible text, so keep
# room for both. Effort "low" keeps the labs cheap and fast; raise it when a
# lab needs deeper reasoning.
DEFAULT_MAX_TOKENS = 4096
DEFAULT_EFFORT = "low"

_ENV_KEY = "ANTHROPIC_API_KEY"


class MissingAPIKeyError(RuntimeError):
    """Raised when the ANTHROPIC_API_KEY environment variable is not set."""


def read_api_key() -> str:
    """Return the API key from the environment.

    Raises:
        MissingAPIKeyError: if the variable is missing or empty.
    """
    key = os.environ.get(_ENV_KEY, "").strip()
    if not key:
        raise MissingAPIKeyError(
            f"{_ENV_KEY} is not set. Copy .env.example to .env, add your key, "
            f"and export it before running this lab. Never commit the key."
        )
    return key


def resolve_model(model: str | None = None) -> str:
    """Return the model id to use for a request."""
    return model or os.environ.get("LAB_MODEL", "").strip() or DEFAULT_MODEL


def get_client() -> Any:
    """Build an Anthropic client, failing early with a clear message.

    Raises:
        MissingAPIKeyError: if the API key is absent.
        ImportError: if the anthropic package is not installed.
    """
    api_key = read_api_key()
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "The anthropic package is not installed. Run 'make setup' or "
            "'pip install -e .' from the lab root."
        ) from exc
    return anthropic.Anthropic(api_key=api_key)


def _build_params(
    messages: list[dict[str, Any]],
    *,
    model: str | None,
    system: str | list[dict[str, Any]] | None,
    max_tokens: int,
    effort: str | None,
    extra: dict[str, Any],
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "model": resolve_model(model),
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system is not None:
        params["system"] = system
    if effort is not None:
        params["output_config"] = {"effort": effort}
    params.update(extra)
    return params


def complete(
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    system: str | list[dict[str, Any]] | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    effort: str | None = DEFAULT_EFFORT,
    **kwargs: Any,
) -> Any:
    """Send one non-streaming Messages API request and return the response.

    The full response object is returned rather than a string so that labs can
    read stop_reason, content blocks, and usage. Use text_of to pull the text.
    """
    client = get_client()
    params = _build_params(
        messages,
        model=model,
        system=system,
        max_tokens=max_tokens,
        effort=effort,
        extra=kwargs,
    )
    return client.messages.create(**params)


def complete_with_tools(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    *,
    model: str | None = None,
    system: str | list[dict[str, Any]] | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    effort: str | None = DEFAULT_EFFORT,
    tool_choice: dict[str, Any] | None = None,
    **kwargs: Any,
) -> Any:
    """Send one Messages API request that exposes tools to the model.

    The caller owns the agentic loop: inspect stop_reason, run any tool_use
    blocks, append the results, and call again.
    """
    client = get_client()
    extra: dict[str, Any] = {"tools": tools}
    if tool_choice is not None:
        extra["tool_choice"] = tool_choice
    extra.update(kwargs)
    params = _build_params(
        messages,
        model=model,
        system=system,
        max_tokens=max_tokens,
        effort=effort,
        extra=extra,
    )
    return client.messages.create(**params)


def stream_text(
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    system: str | list[dict[str, Any]] | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    effort: str | None = DEFAULT_EFFORT,
    **kwargs: Any,
) -> Iterator[str]:
    """Yield text deltas as the model produces them.

    Streaming does not change the answer. It changes when the caller sees the
    first token, which matters for anything a person is waiting on.
    """
    client = get_client()
    params = _build_params(
        messages,
        model=model,
        system=system,
        max_tokens=max_tokens,
        effort=effort,
        extra=kwargs,
    )
    with client.messages.stream(**params) as stream:
        for chunk in stream.text_stream:
            yield chunk


def text_of(response: Any) -> str:
    """Join every text block of a response into a single string.

    Content is a list of blocks, and text is not always the first one, so
    always filter by block type instead of indexing content[0].
    """
    parts = [block.text for block in response.content if block.type == "text"]
    return "".join(parts)


def tool_uses(response: Any) -> list[Any]:
    """Return the tool_use blocks of a response, in order."""
    return [block for block in response.content if block.type == "tool_use"]
