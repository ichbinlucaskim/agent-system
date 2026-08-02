"""Token accounting and cost estimation.

WARNING ABOUT PRICES
--------------------
The numbers in PRICE_TABLE are a snapshot written by hand for teaching
purposes. They are not authoritative and they go stale. Verify every value
against current Anthropic pricing before you trust a number this module
produces, and before you quote a cost to anyone. Treat the output of
estimate_cost as an order of magnitude, not an invoice.

Cache reads and cache writes are priced differently from ordinary input
tokens. The multipliers below are the documented ratios, but the same warning
applies: verify before trusting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# US dollars per one million tokens, as (input, output).
# VERIFY THESE AGAINST CURRENT ANTHROPIC PRICING BEFORE USE.
PRICE_TABLE: dict[str, tuple[float, float]] = {
    "claude-opus-5": (5.00, 25.00),
    "claude-opus-4-8": (5.00, 25.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
}

# Cache read tokens cost a fraction of ordinary input tokens; cache writes cost
# a premium. VERIFY THESE RATIOS BEFORE USE.
CACHE_READ_MULTIPLIER = 0.10
CACHE_WRITE_MULTIPLIER = 1.25

_PER_MILLION = 1_000_000


class UnknownModelError(KeyError):
    """Raised when a model has no entry in PRICE_TABLE."""


@dataclass(frozen=True)
class TokenUsage:
    """Token counts pulled off one or more API responses."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_read_tokens
            + self.cache_creation_tokens
        )

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_read_tokens=self.cache_read_tokens + other.cache_read_tokens,
            cache_creation_tokens=(
                self.cache_creation_tokens + other.cache_creation_tokens
            ),
        )


def usage_of(response: Any) -> TokenUsage:
    """Read a TokenUsage off a Messages API response.

    Note that input_tokens counts only the uncached remainder. The full prompt
    size is input_tokens plus cache reads plus cache writes.
    """
    usage = getattr(response, "usage", None)
    if usage is None:
        return TokenUsage()
    return TokenUsage(
        input_tokens=getattr(usage, "input_tokens", 0) or 0,
        output_tokens=getattr(usage, "output_tokens", 0) or 0,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
        cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
    )


def sum_usage(usages: list[TokenUsage]) -> TokenUsage:
    """Add up a list of TokenUsage values."""
    total = TokenUsage()
    for usage in usages:
        total = total + usage
    return total


def estimate_cost(model: str, usage: TokenUsage) -> float:
    """Estimate the US dollar cost of a usage record.

    Raises:
        UnknownModelError: if the model is not in PRICE_TABLE. Add it there
            after checking the current published price.
    """
    if model not in PRICE_TABLE:
        raise UnknownModelError(
            f"No price entry for {model!r}. Add one to PRICE_TABLE in "
            f"common/cost.py after verifying the current published price."
        )
    input_price, output_price = PRICE_TABLE[model]
    dollars = (
        usage.input_tokens * input_price
        + usage.cache_read_tokens * input_price * CACHE_READ_MULTIPLIER
        + usage.cache_creation_tokens * input_price * CACHE_WRITE_MULTIPLIER
        + usage.output_tokens * output_price
    )
    return dollars / _PER_MILLION


def format_cost_report(model: str, usage: TokenUsage) -> str:
    """Render a short human readable cost summary."""
    lines = [
        f"model                 {model}",
        f"input tokens          {usage.input_tokens}",
        f"output tokens         {usage.output_tokens}",
        f"cache read tokens     {usage.cache_read_tokens}",
        f"cache write tokens    {usage.cache_creation_tokens}",
    ]
    try:
        dollars = estimate_cost(model, usage)
    except UnknownModelError as exc:
        lines.append(f"estimated cost        unavailable ({exc.args[0]})")
    else:
        lines.append(f"estimated cost        ${dollars:.6f} (verify prices)")
    return "\n".join(lines)
