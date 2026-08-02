"""Lab 00 - Setup (reference solution).

Makes a first Claude API call, contrasts streaming with non-streaming, and
reads token usage off the response.
"""

from __future__ import annotations

import sys
from typing import Any

from common.client import (
    MissingAPIKeyError,
    complete,
    read_api_key,
    resolve_model,
    stream_text,
    text_of,
)

QUESTION = "In two sentences, what is an agent in the context of LLM systems?"


def mask(api_key: str) -> str:
    """Return a display-safe version of an API key."""
    if len(api_key) < 12:
        # Too short to reveal anything from safely. Show nothing.
        return "." * 8
    return f"{api_key[:7]}{'.' * 8}{api_key[-4:]}"


def check_api_key() -> str:
    """Read the API key from the environment and return a masked form."""
    return mask(read_api_key())


def ask(question: str) -> Any:
    """Send one non-streaming Messages API request and return the response."""
    return complete([{"role": "user", "content": question}])


def ask_streaming(question: str) -> str:
    """Send one streaming request and return the assembled text."""
    return "".join(stream_text([{"role": "user", "content": question}]))


def usage_summary(response: Any) -> dict[str, int]:
    """Return token counts from a response as a plain dict."""
    usage = getattr(response, "usage", None)
    summary = {
        "input_tokens": getattr(usage, "input_tokens", 0) or 0,
        "output_tokens": getattr(usage, "output_tokens", 0) or 0,
        "cache_read_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
        "cache_creation_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
    }
    summary["total_tokens"] = sum(summary.values())
    return summary


def main() -> int:
    """Run the whole lab end to end and print what happened."""
    try:
        print(f"api key    {check_api_key()}")
    except MissingAPIKeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"model      {resolve_model()}")

    print("\n-- non-streaming --")
    response = ask(QUESTION)
    print(text_of(response))
    print(f"stop_reason {response.stop_reason}")
    for key, value in usage_summary(response).items():
        print(f"{key:<24}{value}")

    print("\n-- streaming --")
    # The same answer, but the first characters appear immediately instead of
    # after the whole response is generated.
    for delta in stream_text([{"role": "user", "content": QUESTION}]):
        print(delta, end="", flush=True)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
