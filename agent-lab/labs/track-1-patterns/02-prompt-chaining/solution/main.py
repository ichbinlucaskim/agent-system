"""Lab 02 - Prompt chaining (reference solution).

A chain is a fixed sequence of model calls where each call consumes the
previous output. The sequence lives in code, and the gate between steps is
ordinary Python, which is what stops one bad intermediate result from being
paid for twice downstream.
"""

from __future__ import annotations

from typing import Any

from common.client import complete, text_of
from common.tracing import Trace

# A requirement shorter than this many words is almost always too vague to
# act on, and vague requirements are exactly what the gate exists to catch.
MIN_WORDS_PER_REQUIREMENT = 4


def extract_requirements(brief: str) -> list[str]:
    """Turn a free-form brief into a list of short requirement strings."""
    system = (
        "You extract product requirements from a brief. Return one "
        "requirement per line as plain text, with no numbering and no "
        "bullets. Each requirement must be a single specific, actionable "
        "sentence. Return nothing except the requirements."
    )
    response = complete([{"role": "user", "content": brief}], system=system)
    # Strip bullet characters anyway: instructions reduce formatting drift,
    # they do not eliminate it, and the gate should judge content, not markup.
    lines = [line.strip(" \t-*") for line in text_of(response).splitlines()]
    return [line for line in lines if line]


def gate_requirements(requirements: list[str]) -> tuple[bool, str]:
    """Deterministic check between step one and step two. Returns (ok, reason)."""
    if not requirements:
        return (False, "gate failed: nothing was extracted from the brief.")
    vague = [
        item
        for item in requirements
        if len(item.split()) < MIN_WORDS_PER_REQUIREMENT
    ]
    if vague:
        listed = "; ".join(repr(item) for item in vague)
        return (
            False,
            f"gate failed: too vague to act on ({listed}). A requirement "
            f"needs at least {MIN_WORDS_PER_REQUIREMENT} words.",
        )
    return (True, f"gate passed: {len(requirements)} actionable requirements.")


def draft_spec(requirements: list[str]) -> str:
    """Draft a specification from the gated requirements only."""
    # The draft sees the gated list, not the original brief. Each step gets
    # only what it needs, so a bad draft traces back to a bad list.
    numbered = "\n".join(
        f"{index}. {item}" for index, item in enumerate(requirements, 1)
    )
    system = (
        "You write a short product specification from a fixed list of "
        "requirements. Cover every requirement, add nothing that is not on "
        "the list, and use plain prose with a short section per requirement."
    )
    response = complete([{"role": "user", "content": numbered}], system=system)
    return text_of(response)


def polish_spec(spec: str) -> str:
    """Rewrite the draft for clarity without adding requirements."""
    system = (
        "You are a copy editor. Rewrite the specification for clarity and "
        "concision. Change wording only: do not add, remove, or reinterpret "
        "any requirement. The set of requirements must be identical before "
        "and after your edit."
    )
    response = complete([{"role": "user", "content": spec}], system=system)
    return text_of(response)


def run_chain(
    brief: str,
    *,
    max_retries: int = 1,
    trace: Trace | None = None,
) -> dict[str, Any]:
    """Run the full chain and return every intermediate output."""
    trace = Trace("prompt-chain") if trace is None else trace
    result: dict[str, Any] = {
        "requirements": [],
        "gate": (False, "gate never ran"),
        "draft": "",
        "final": "",
        "stopped_at": None,
    }

    # Retry only the step that failed. Rerunning the whole chain would pay
    # again for steps that already succeeded.
    for attempt in range(max_retries + 1):
        with trace.step("extract_requirements", attempt=attempt) as step:
            result["requirements"] = extract_requirements(brief)
            step.output = result["requirements"]
        result["gate"] = gate_requirements(result["requirements"])
        if result["gate"][0]:
            break

    if not result["gate"][0]:
        # Stopping here is the point of the gate: a draft built on bad
        # requirements costs two more calls and still gets thrown away.
        result["stopped_at"] = "gate_requirements"
        return result

    with trace.step("draft_spec") as step:
        result["draft"] = draft_spec(result["requirements"])
        step.output = result["draft"]

    with trace.step("polish_spec") as step:
        result["final"] = polish_spec(result["draft"])
        step.output = result["final"]

    return result


def main() -> int:
    """Run the chain on one brief and show every intermediate output."""
    brief = (
        "We need a small web page where customers can check the status of an "
        "order. It should work well on phones, load quickly even on a slow "
        "connection, and let the customer request an email update when the "
        "order is late."
    )
    trace = Trace("prompt-chain")
    result = run_chain(brief, trace=trace)

    print(f"requirements ({len(result['requirements'])}):")
    for item in result["requirements"]:
        print(f"  - {item}")
    print(f"gate: {result['gate'][1]}")

    if result["stopped_at"] is not None:
        print(f"chain stopped at {result['stopped_at']}")
        print(trace.render_text_report())
        return 1

    print(f"\nfinal specification:\n{result['final']}\n")
    print(trace.render_text_report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
