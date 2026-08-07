"""Route FAQ questions to a cheap path and account changes to the agent loop."""

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
    """Return 'faq' or 'account'.

    Mentions of a concrete order id or an irreversible verb go to the agent
    path. Pure policy questions stay on the FAQ path.
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
