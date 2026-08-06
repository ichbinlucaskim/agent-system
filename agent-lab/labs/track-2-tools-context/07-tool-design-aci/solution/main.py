"""Lab 07 - Tool design and the agent-computer interface (reference solution).

The model sees exactly three things about a tool: its name, its description,
and its input schema. This lab writes the same capability twice, once designed
and once careless, and measures the difference in selection accuracy.
"""

from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from common.client import MissingAPIKeyError, complete_with_tools, tool_uses

INVENTORY: dict[str, int] = {
    "SKU-100": 12,
    "SKU-200": 0,
    "SKU-300": 47,
}

PRODUCT_DOCS: dict[str, str] = {
    "SKU-100": (
        "Recycled steel bottle, 750 ml, 24 cm tall. Hand wash only. "
        "Two year warranty."
    ),
    "SKU-200": (
        "Recycled steel tumbler, 400 ml, 15 cm tall. Dishwasher safe. "
        "Two year warranty."
    ),
    "SKU-300": (
        "Replacement silicone lid, fits SKU-100 and SKU-200. Dishwasher "
        "safe. Sold without a warranty."
    ),
}

# The tool the stock tool competes with. It is held identical across every
# variant below, so any difference in the rates belongs to the stock tool.
# Without a competitor there is nothing to measure: a lone tool gets called
# for anything vaguely related to it, and even a one-word description scores
# a perfect rate.
#
# It is an ordinary search tool taking free text, which is what leaves the
# boundary between the two tools genuinely open. Give this one a closed SKU
# enum as well and it becomes obviously right for every specification
# question on its own, the rates all saturate at 1.00, and the experiment
# goes quiet again. Measuring a wording change needs cases the wording has
# to decide.
DOCS_TOOL: dict[str, Any] = {
    "name": "search_product_docs",
    "description": (
        "Search the product documentation for specifications, materials, "
        "warranty terms, dimensions, and care instructions."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
        },
        "required": ["query"],
    },
}

# Says when to call, not only what the tool can do, and rules out the cases
# that belong to the other tool.
TRIGGER_DESCRIPTION = (
    "Look up the current number of units in stock for one SKU. "
    "Call this whenever the user asks whether something is available, "
    "in stock, or how many are left. Stock changes constantly, so "
    "never answer a stock question from general knowledge. This tool "
    "knows nothing about materials, sizes, care instructions, or warranty "
    "terms."
)

# States a capability and nothing else. The model has to guess when it
# applies, which in practice means guessing generously.
CAPABILITY_DESCRIPTION = "Look up stock."

CLOSED_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "sku": {
            "type": "string",
            "description": "The SKU identifier to look up.",
            # A closed set makes the wrong call hard to express: the model
            # cannot invent a SKU the schema will accept. The enum doubles
            # as documentation, which is why it moves the selection rate
            # and not just the argument quality.
            "enum": sorted(INVENTORY),
        }
    },
    "required": ["sku"],
}

LOOSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "sku": {"type": "string"},
    },
}


def _stock_tool(description: str, input_schema: dict[str, Any]) -> dict[str, Any]:
    """Build one variant of the stock tool.

    Every variant shares the name, so the experiment isolates the two fields
    it varies. Renaming is a separate experiment (see Going further).
    """
    return {
        "name": "get_stock_level",
        "description": description,
        "input_schema": copy.deepcopy(input_schema),
    }


# Four variants, so the contribution of each change can be read on its own
# rather than as one bundle. Measured over three runs of CASES: vague 0.70,
# trigger wording alone 0.97, closed schema alone 0.93, both 1.00. Neither
# field dominates, which is the point: the schema is documentation too.
GOOD_TOOL = _stock_tool(TRIGGER_DESCRIPTION, CLOSED_SCHEMA)
VAGUE_TOOL = _stock_tool(CAPABILITY_DESCRIPTION, LOOSE_SCHEMA)
TRIGGER_ONLY_TOOL = _stock_tool(TRIGGER_DESCRIPTION, LOOSE_SCHEMA)
SCHEMA_ONLY_TOOL = _stock_tool(CAPABILITY_DESCRIPTION, CLOSED_SCHEMA)

# (question, expected tool name or None). None means a correct run answers
# directly without calling any tool. The cases sit on the boundary between
# the two tools on purpose: questions that name a SKU but ask about
# something the stock tool cannot answer are where a vague description does
# its damage, by pulling work away from the tool that should have it.
CASES: list[tuple[str, str | None]] = [
    ("Do you have SKU-200 in stock right now?", "get_stock_level"),
    ("How many units of SKU-100 are left?", "get_stock_level"),
    ("Is SKU-300 available for pickup today?", "get_stock_level"),
    ("Can I still buy SKU-100, or is it sold out?", "get_stock_level"),
    ("What material is SKU-100 made of?", "search_product_docs"),
    ("What does the warranty on SKU-200 cover?", "search_product_docs"),
    ("What are the dimensions of SKU-300?", "search_product_docs"),
    ("How should I clean SKU-100?", "search_product_docs"),
    ("What does a 12 month warranty usually cover?", None),
    ("Write a one sentence thank you note to a customer.", None),
]


def select_tool(question: str, tools: list[dict[str, Any]]) -> str | None:
    """Return the name of the tool the model chose, or None if it answered directly."""
    response = complete_with_tools([{"role": "user", "content": question}], tools)
    chosen = tool_uses(response)
    # Answering without a tool is a real outcome, not an error: for some
    # questions the correct behaviour is to call nothing.
    if not chosen:
        return None
    return chosen[0].name


def selection_rate(
    cases: list[tuple[str, str | None]], tools: list[dict[str, Any]]
) -> float:
    """Fraction of cases where the expected tool was selected."""
    if not cases:
        return 0.0
    # The cases are independent, so they run concurrently the way lab 04 ran
    # its sections. A serial version of this experiment takes minutes, and an
    # experiment nobody reruns stops being a measurement.
    with ThreadPoolExecutor(max_workers=min(8, len(cases))) as pool:
        chosen = list(pool.map(lambda case: select_tool(case[0], tools), cases))
    matches = sum(
        1 for (_, expected), got in zip(cases, chosen) if got == expected
    )
    return matches / len(cases)


def compare_descriptions(cases: list[tuple[str, str | None]]) -> dict[str, float]:
    """Run the same cases against all four variants of the stock tool."""
    # The questions and the competing docs tool are held fixed and only the
    # stock tool varies, so any difference in the rates belongs to it. The
    # two middle variants change one field each, which is what makes the
    # contribution of the wording and of the schema separable.
    variants = {
        "vague": VAGUE_TOOL,
        "trigger_only": TRIGGER_ONLY_TOOL,
        "schema_only": SCHEMA_ONLY_TOOL,
        "good": GOOD_TOOL,
    }
    return {
        name: selection_rate(cases, [tool, DOCS_TOOL])
        for name, tool in variants.items()
    }


def format_tool_error(problem: str, valid_options: list[str]) -> str:
    """Turn a tool failure into a message the model can recover from."""
    options = ", ".join(valid_options) if valid_options else "none"
    # The error text is the next thing the model reads, so it is a prompt:
    # name what went wrong and spell out what a valid call looks like.
    return (
        f"Error: {problem}. Valid options are: {options}. "
        "Retry the call with one of these values."
    )


def run_tool(name: str, tool_input: dict[str, Any]) -> tuple[str, bool]:
    """Execute one tool call. Returns (result_text, is_error)."""
    if name == "get_stock_level":
        sku = str(tool_input.get("sku", "")).strip().upper()
        if sku not in INVENTORY:
            return (format_tool_error(f"unknown SKU {sku!r}", sorted(INVENTORY)), True)
        return (f"{sku} has {INVENTORY[sku]} units in stock.", False)
    if name == "search_product_docs":
        # The free-text parameter is the price of leaving this tool ordinary:
        # the SKU has to be recovered from the query instead of being handed
        # over by the schema.
        query = str(tool_input.get("query", "")).strip().upper()
        found = [sku for sku in sorted(PRODUCT_DOCS) if sku in query]
        if not found:
            return (
                format_tool_error(
                    f"no known SKU appears in query {query!r}", sorted(PRODUCT_DOCS)
                ),
                True,
            )
        return (PRODUCT_DOCS[found[0]], False)
    return (
        format_tool_error(
            f"unknown tool {name!r}", ["get_stock_level", "search_product_docs"]
        ),
        True,
    )


def main() -> int:
    """Run the description experiment and print both selection rates."""
    print("a recoverable tool error looks like this:")
    output, _ = run_tool("get_stock_level", {"sku": "SKU-999"})
    print(f"  {output}\n")

    try:
        rates = compare_descriptions(CASES)
    except MissingAPIKeyError as error:
        print(f"skipping the live comparison: {error}")
        return 0

    print("selection rate, competing against the docs tool:")
    for name in ("vague", "trigger_only", "schema_only", "good"):
        print(f"  {name:<13} {rates[name]:.2f}")
    print("\nwhat each change recovered on its own:")
    print(f"  trigger wording  {rates['trigger_only'] - rates['vague']:+.2f}")
    print(f"  closed schema    {rates['schema_only'] - rates['vague']:+.2f}")
    print(f"  both together    {rates['good'] - rates['vague']:+.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
