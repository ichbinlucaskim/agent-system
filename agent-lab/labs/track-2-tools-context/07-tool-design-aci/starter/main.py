"""Lab 07 - Tool design and the agent-computer interface (starter).

Goal: Design the agent-computer interface deliberately: name tools clearly, write schemas and descriptions that say when to call a tool rather than only what it does, turn error messages into recovery instructions, and measure how much a bad description degrades tool selection.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-2-tools-context/07-tool-design-aci/tests -v
"""

from __future__ import annotations

from typing import Any

INVENTORY: dict[str, int] = {"SKU-100": 12, "SKU-200": 0, "SKU-300": 47}

# TODO: step 1. A second tool for the stock tool to compete with, holding a
# capability the stock tool does not have (product specifications, say). Keep
# it identical across every variant below. Without a competitor there is
# nothing to measure: a lone tool gets selected for anything vaguely related
# to it, and even a one-word description scores a perfect rate.
DOCS_TOOL: dict[str, Any] = {}

# TODO: step 1. Four variants of the same stock tool, sharing one name so the
# name cannot explain any difference. GOOD says when to call and rules out
# what belongs to the other tool, and closes its input space with an enum.
# VAGUE states a capability and accepts any string. The two middle variants
# change one field each, which is what makes step 6 answerable: with only
# GOOD and VAGUE the fields move together and no single change can be
# credited.
GOOD_TOOL: dict[str, Any] = {}
VAGUE_TOOL: dict[str, Any] = {}
TRIGGER_ONLY_TOOL: dict[str, Any] = {}
SCHEMA_ONLY_TOOL: dict[str, Any] = {}

# TODO: step 1. (question, expected tool name or None). Put cases on the
# boundary between the two tools: questions naming a SKU but asking about
# something the stock tool cannot answer are where a vague description does
# its damage, by pulling work away from the tool that should have had it.
CASES: list[tuple[str, str | None]] = []


def select_tool(question: str, tools: list[dict[str, Any]]) -> str | None:
    """Return the name of the tool the model chose, or None if it answered directly."""
    # TODO: step 2. Make one call with the given tools, read the tool_use blocks, and return the first tool name. Answering without a tool is a real outcome, not an error.
    raise NotImplementedError


def selection_rate(cases: list[tuple[str, str | None]], tools: list[dict[str, Any]]) -> float:
    """Fraction of cases where the expected tool was selected."""
    # TODO: step 3. Each case is (question, expected_tool_name_or_None). Divide matches by total; an empty list returns 0.0 rather than dividing by zero. The cases are independent, so run them concurrently the way lab 04 ran its sections: serial, this experiment takes minutes, and an experiment nobody reruns stops being a measurement.
    raise NotImplementedError


def compare_descriptions(cases: list[tuple[str, str | None]]) -> dict[str, float]:
    """Run the same cases against all four variants of the stock tool."""
    # TODO: step 4. Hold the questions and the competing docs tool fixed and vary only the stock tool. Return {'vague': rate, 'trigger_only': rate, 'schema_only': rate, 'good': rate} so each change can be credited on its own.
    raise NotImplementedError


def format_tool_error(problem: str, valid_options: list[str]) -> str:
    """Turn a tool failure into a message the model can recover from."""
    # TODO: step 5. Name what went wrong and list the valid inputs. The error text is the next thing the model reads, so treat it as a prompt.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
