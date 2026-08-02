"""Lab 00 - Setup (starter).

Goal: make your first Claude API call, see the difference between a streaming
and a non-streaming request, and read token usage off the response.

Fill in each function below. Every one of them has a TODO describing what to
do. Run the tests with:

    pytest labs/00-setup/tests -v
"""

from __future__ import annotations

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
    """Return a display-safe version of an API key.

    Keep the first 7 and last 4 characters, replace the middle with dots.
    A key shorter than 12 characters returns just dots, never the raw value.
    """
    # TODO: step 1. Implement masking so a key can be shown in a log or a
    # terminal without leaking it. Never return the full key.
    raise NotImplementedError


def check_api_key() -> str:
    """Read the API key from the environment and return a masked form.

    Let MissingAPIKeyError propagate. The point of this step is that a missing
    credential should fail loudly and early, not halfway through a run.
    """
    # TODO: step 2. Call read_api_key from common.client, then return mask(key).
    raise NotImplementedError


def ask(question: str) -> Any:
    """Send one non-streaming Messages API request and return the response.

    Return the whole response object, not a string, so the caller can read
    stop_reason and usage.
    """
    # TODO: step 3. Call complete() with a single user message holding the
    # question. Return the response object unchanged.
    raise NotImplementedError


def ask_streaming(question: str) -> str:
    """Send one streaming request and return the assembled text.

    The answer is the same as the non-streaming call. What changes is that the
    caller sees the first token far sooner.
    """
    # TODO: step 4. Iterate stream_text() and join the deltas into one string.
    raise NotImplementedError


def usage_summary(response: Any) -> dict[str, int]:
    """Return token counts from a response as a plain dict.

    Keys: input_tokens, output_tokens, cache_read_tokens,
    cache_creation_tokens, total_tokens. Missing fields count as 0.

    Remember that input_tokens is the uncached remainder only. The full prompt
    size is input plus cache reads plus cache writes.
    """
    # TODO: step 5. Read response.usage defensively with getattr and build the
    # dict. total_tokens is the sum of the other four.
    raise NotImplementedError


def main() -> int:
    """Run the whole lab end to end and print what happened."""
    # TODO: step 6. Print the masked key, run ask(), print the text via
    # text_of(), print the usage summary, then run ask_streaming() and print
    # the deltas as they arrive. Return 0 on success and 1 on
    # MissingAPIKeyError.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
