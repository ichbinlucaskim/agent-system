"""Lab 01 - The augmented LLM (reference solution).

An augmented LLM is a plain model call plus retrieval, tools, and memory.
Everything later in this course is built out of this one shape.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from common.client import complete_with_tools, text_of, tool_uses


@dataclass(frozen=True)
class Document:
    """One retrievable document."""

    id: str
    text: str


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


@dataclass
class Memory:
    """The conversation so far, trimmed to a fixed number of turns."""

    max_turns: int = 6
    turns: list[dict[str, str]] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        """Append one turn and drop the oldest if over max_turns."""
        self.turns.append({"role": role, "content": content})
        if len(self.turns) > self.max_turns:
            # Memory is a budget, not an archive. Oldest turns fall off first.
            del self.turns[: len(self.turns) - self.max_turns]

    def messages(self) -> list[dict[str, Any]]:
        """Return the remembered turns as a fresh messages list."""
        return [dict(turn) for turn in self.turns]


def tokenize(text: str) -> set[str]:
    """Lowercase a string and return its set of word tokens."""
    return set(re.findall(r"\w+", text.lower()))


def retrieve(query: str, documents: list[Document], k: int = 2) -> list[Document]:
    """Return the k documents sharing the most tokens with the query."""
    query_tokens = tokenize(query)
    scored = [
        (len(query_tokens & tokenize(document.text)), index, document)
        for index, document in enumerate(documents)
    ]
    # Drop zero-overlap documents: padding the context with irrelevant text
    # costs tokens and invites the model to use it.
    hits = [item for item in scored if item[0] > 0]
    hits.sort(key=lambda item: (-item[0], item[1]))
    return [document for _, _, document in hits[:k]]


def build_system(context: list[Document]) -> str:
    """Build the system prompt from the retrieved documents."""
    if context:
        blocks = "\n\n".join(f"[{doc.id}] {doc.text}" for doc in context)
    else:
        blocks = "(no documents matched this question)"
    return (
        "You answer questions about a hardware store using only the reference "
        "documents below and the tools you are given.\n\n"
        "Rules:\n"
        "- Cite the document id in square brackets for any claim taken from a "
        "document.\n"
        "- For stock or availability questions, call get_stock_level. The "
        "documents do not contain stock levels.\n"
        "- If neither the documents nor the tools support an answer, say you "
        "do not know.\n\n"
        f"Reference documents:\n{blocks}"
    )


def run_tool(name: str, tool_input: dict[str, Any]) -> tuple[str, bool]:
    """Execute one tool call. Returns (result_text, is_error)."""
    if name != "get_stock_level":
        return (f"Error: unknown tool {name!r}.", True)
    sku = str(tool_input.get("sku", "")).strip().upper()
    if sku not in INVENTORY:
        known = ", ".join(sorted(INVENTORY))
        # An error the model can act on: it names the valid inputs.
        return (f"Error: unknown SKU {sku!r}. Known SKUs are: {known}.", True)
    return (f"{sku} has {INVENTORY[sku]} units in stock.", False)


def augmented_call(
    question: str,
    documents: list[Document] | None = None,
    memory: Memory | None = None,
    *,
    k: int = 2,
    max_tool_rounds: int = 3,
) -> str:
    """Answer one question with retrieval, tools, and memory attached."""
    documents = CORPUS if documents is None else documents
    memory = Memory() if memory is None else memory

    context = retrieve(question, documents, k)
    system = build_system(context)

    memory.add("user", question)
    messages: list[dict[str, Any]] = memory.messages()

    response = None
    for _ in range(max_tool_rounds):
        response = complete_with_tools(messages, TOOLS, system=system)
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            break
        # Every tool_use block needs exactly one tool_result, and all results
        # go back in a single user message.
        results: list[dict[str, Any]] = []
        for block in tool_uses(response):
            output, is_error = run_tool(block.name, dict(block.input))
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                    "is_error": is_error,
                }
            )
        messages.append({"role": "user", "content": results})

    answer = text_of(response) if response is not None else ""
    memory.add("assistant", answer)
    return answer


def main() -> int:
    """Run one grounded question and one tool question."""
    memory = Memory()

    grounded = "How long do I have to return something?"
    print(f"user      {grounded}")
    print(f"assistant {augmented_call(grounded, memory=memory)}\n")

    tool_question = "Do you have SKU-200 available right now?"
    print(f"user      {tool_question}")
    print(f"assistant {augmented_call(tool_question, memory=memory)}\n")

    print(f"memory holds {len(memory.turns)} turns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
