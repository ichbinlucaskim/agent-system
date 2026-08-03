"""Lab 07 - Tool design and the agent-computer interface (reference solution).

The model sees exactly three things about a tool: its name, its description,
and its input schema. This lab writes the same capability twice, once designed
and once careless, and measures the difference in selection accuracy.
"""

from __future__ import annotations

from typing import Any

from common.client import MissingAPIKeyError, complete_with_tools, tool_uses

INVENTORY: dict[str, int] = {
    "SKU-100": 12,
    "SKU-200": 0,
    "SKU-300": 47,
}

# Both variants share the tool name so the experiment isolates the description
# and the schema. Renaming is a separate experiment (see Going further).
GOOD_TOOL: dict[str, Any] = {
    "name": "get_stock_level",
    "description": (
        "Look up the current number of units in stock for one SKU. "
        "Call this whenever the user asks whether something is available, "
        "in stock, or how many are left. Stock changes constantly, so "
        "never answer a stock question from general knowledge."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "sku": {
                "type": "string",
                "description": "The SKU identifier to look up.",
                # A closed set makes the wrong call hard to express: the
                # model cannot invent a SKU the schema will accept.
                "enum": sorted(INVENTORY),
            }
        },
        "required": ["sku"],
    },
}

VAGUE_TOOL: dict[str, Any] = {
    "name": "get_stock_level",
    # States a capability, never a trigger. The model has to guess when
    # this applies, and the loose schema accepts any string as input.
    "description": "Look up stock.",
    "input_schema": {
        "type": "object",
        "properties": {
            "sku": {"type": "string"},
        },
    },
}

# (question, expected tool name or None). None means a correct run answers
# directly without calling any tool.
CASES: list[tuple[str, str | None]] = [
    ("Do you have SKU-200 in stock right now?", "get_stock_level"),
    ("How many units of SKU-100 are left?", "get_stock_level"),
    ("Is SKU-300 available for pickup today?", "get_stock_level"),
    ("Can I still buy SKU-100, or is it sold out?", "get_stock_level"),
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
    matches = sum(
        1 for question, expected in cases if select_tool(question, tools) == expected
    )
    return matches / len(cases)


def compare_descriptions(cases: list[tuple[str, str | None]]) -> dict[str, float]:
    """Run the same cases against the good and vague tool definitions."""
    # The questions are held fixed and only the tool definition varies, so
    # any difference in the rates is attributable to the definition alone.
    return {
        "good": selection_rate(cases, [GOOD_TOOL]),
        "vague": selection_rate(cases, [VAGUE_TOOL]),
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
    if name != "get_stock_level":
        return (format_tool_error(f"unknown tool {name!r}", ["get_stock_level"]), True)
    sku = str(tool_input.get("sku", "")).strip().upper()
    if sku not in INVENTORY:
        return (format_tool_error(f"unknown SKU {sku!r}", sorted(INVENTORY)), True)
    return (f"{sku} has {INVENTORY[sku]} units in stock.", False)


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

    print(f"selection rate, good description   {rates['good']:.2f}")
    print(f"selection rate, vague description  {rates['vague']:.2f}")
    print(f"difference                         {rates['good'] - rates['vague']:+.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
