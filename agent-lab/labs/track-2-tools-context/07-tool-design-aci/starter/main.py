"""Lab 07 - Tool design and the agent-computer interface (starter).

Goal: Design the agent-computer interface deliberately: name tools clearly, write schemas and descriptions that say when to call a tool rather than only what it does, turn error messages into recovery instructions, and measure how much a bad description degrades tool selection.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-2-tools-context/07-tool-design-aci/tests -v
"""

from __future__ import annotations

from typing import Any


def select_tool(question: str, tools: list[dict[str, Any]]) -> str | None:
    """Return the name of the tool the model chose, or None if it answered directly."""
    # TODO: step 2. Make one call with the given tools, read the tool_use blocks, and return the first tool name. Answering without a tool is a real outcome, not an error.
    raise NotImplementedError


def selection_rate(cases: list[tuple[str, str | None]], tools: list[dict[str, Any]]) -> float:
    """Fraction of cases where the expected tool was selected."""
    # TODO: step 3. Each case is (question, expected_tool_name_or_None). Divide matches by total; an empty list returns 0.0 rather than dividing by zero.
    raise NotImplementedError


def compare_descriptions(cases: list[tuple[str, str | None]]) -> dict[str, float]:
    """Run the same cases against the good and vague tool definitions."""
    # TODO: step 4. Hold the questions fixed and vary only the tool definition. Return {'good': rate, 'vague': rate} so the difference is one subtraction away.
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
