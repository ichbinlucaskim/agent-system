"""Lab 01 - The augmented LLM (starter).

Goal: build the base building block that every later lab reuses. An augmented
LLM is a plain model call plus three attachments: retrieval (facts pulled in
from a corpus), tools (actions the model can invoke), and memory (what was
said before).

Fill in each function below. Run the tests with:

    pytest labs/track-1-patterns/01-augmented-llm/tests -v
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from common.client import complete_with_tools, text_of, tool_uses

# Live state that no document can hold: the tool exists so the model can read
# a number that changes after the corpus was written.
INVENTORY: dict[str, int] = {
    "SKU-100": 12,
    "SKU-200": 0,
    "SKU-300": 47,
}

TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_stock_level",
        "description": (
            "Look up the current number of units in stock for one SKU. "
            "Call this whenever the user asks whether something is available, "
            "in stock, or how many are left. Stock changes constantly, so "
            "never answer from the documents for a stock question."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {
                    "type": "string",
                    "description": "The SKU identifier, for example SKU-100.",
                }
            },
            "required": ["sku"],
        },
    }
]


@dataclass(frozen=True)
class Document:
    """One retrievable document."""

    id: str
    text: str


# A tiny corpus standing in for a real document store.
CORPUS: list[Document] = [
    Document(
        "returns-policy",
        "Returns are accepted within 30 days of delivery. Refunds are issued "
        "to the original payment method within 5 business days of receipt.",
    ),
    Document(
        "shipping-policy",
        "Standard shipping takes 3 to 5 business days. Express shipping "
        "arrives the next business day for orders placed before 2pm.",
    ),
    Document(
        "warranty-policy",
        "Hardware carries a 12 month warranty covering manufacturing defects. "
        "Accidental damage is not covered by the warranty.",
    ),
]


@dataclass
class Memory:
    """The conversation so far, trimmed to a fixed number of turns."""

    max_turns: int = 6
    turns: list[dict[str, str]] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        """Append one turn and drop the oldest if over max_turns."""
        # TODO: step 3. Append {"role": role, "content": content} and keep only
        # the last max_turns entries. Memory is a budget, not an archive.
        raise NotImplementedError

    def messages(self) -> list[dict[str, Any]]:
        """Return the remembered turns as a fresh messages list."""
        # TODO: step 3. Return a copy so callers cannot mutate the memory.
        raise NotImplementedError


def tokenize(text: str) -> set[str]:
    """Lowercase a string and return its set of word tokens."""
    # TODO: step 1. Use re.findall to pull out word characters, lowercase them,
    # and return them as a set.
    raise NotImplementedError


def retrieve(query: str, documents: list[Document], k: int = 2) -> list[Document]:
    """Return the k documents sharing the most tokens with the query.

    Documents with no overlap are dropped rather than padded in. Ties keep
    corpus order so the result is deterministic.
    """
    # TODO: step 1. Score each document by len(tokenize(query) & tokenize(doc)),
    # drop zero scores, sort by score descending, and return the top k.
    raise NotImplementedError


def build_system(context: list[Document]) -> str:
    """Build the system prompt from the retrieved documents.

    Retrieved text goes in the system prompt, labelled with its document id so
    the model can cite it and so a reader can tell what was grounded.
    """
    # TODO: step 2. Return an instruction plus one block per document in the
    # form "[<id>] <text>". Say that unsupported claims must be refused.
    raise NotImplementedError


def run_tool(name: str, tool_input: dict[str, Any]) -> tuple[str, bool]:
    """Execute one tool call. Returns (result_text, is_error).

    An error is returned as a normal result with is_error set, not raised. The
    model can recover from a message it can read.
    """
    # TODO: step 4. Handle "get_stock_level" against INVENTORY. Return a clear
    # error string for an unknown SKU and for an unknown tool name.
    raise NotImplementedError


def augmented_call(
    question: str,
    documents: list[Document] | None = None,
    memory: Memory | None = None,
    *,
    k: int = 2,
    max_tool_rounds: int = 3,
) -> str:
    """Answer one question with retrieval, tools, and memory attached."""
    # TODO: step 5. Retrieve context, build the system prompt, add the question
    # to memory, then loop: call complete_with_tools, append the assistant
    # content, and if stop_reason is "tool_use" run every tool_use block and
    # append all results in a single user message. Stop when the model stops
    # asking for tools or when max_tool_rounds is reached. Save the answer to
    # memory and return it.
    raise NotImplementedError


def main() -> int:
    """Run one grounded question and one tool question."""
    # TODO: step 6. Build a Memory, ask a question the corpus answers, then ask
    # a stock question that forces a tool call, and print both answers.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
