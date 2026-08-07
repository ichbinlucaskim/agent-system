"""Route FAQ questions to a cheap path and account changes to the agent loop.

Purpose
    Classify a customer message as ``faq`` or ``account`` using order-id and
    irreversible-verb heuristics before any model call.

Why
    This is the routing layer: spend and risk should match intent. Pure policy
    questions skip the tool loop; refund/cancel/escalate/wipe signals and
    concrete ``ORD-…`` ids take the agent path where gates apply.

Trade-offs
    Keyword sets are English and brittle. Mentions of ``ord`` without digits
    still go to account. No ML classifier—predictable for eval, weaker on
    paraphrase.

Edges
    Empty-ish messages with no hints return ``faq`` (input guardrails usually
    run first). Matching is case-insensitive.
"""

from __future__ import annotations

import re

ACCOUNT_HINTS: frozenset[str] = frozenset(
    {
        "refund",
        "cancel",
        "cancellation",
        "wipe",
        "escalate",
        "supervisor",
        "ord-",
    }
)


def route(message: str) -> str:
    """Return 'faq' or 'account' for one customer message.

    Purpose
        Pick the cheap FAQ path vs the account agent loop.

    Why
        Mentions of a concrete order id or an irreversible verb go to the agent
        path. Pure policy questions stay on the FAQ path.

    Trade-offs
        ``ACCOUNT_HINTS`` documents intent but the live check uses an inline
        token set plus regex—keep them aligned when extending.

    Edges
        ``ORD-123`` style ids force account. Token ``ord`` alone also forces
        account. Otherwise faq.
    """
    text = message.lower()
    if re.search(r"\bord-\d+\b", text):
        return "account"
    tokens = set(re.findall(r"\w+", text))
    # ORD tokens already handled; also catch refund/cancel verbs.
    if tokens & {"refund", "refunds", "cancel", "cancelled", "cancellation", "wipe", "escalate", "supervisor"}:
        return "account"
    if "ord" in tokens:
        return "account"
    return "faq"
