# Lab 07 - Tool design and the agent-computer interface

## Goal

After this lab you can design the agent-computer interface deliberately: name tools clearly, write schemas and descriptions that say when to call a tool rather than only what it does, turn error messages into recovery instructions, and measure how much a bad description degrades tool selection.

## Prerequisites

Labs 00 through 06, especially the tool loop from lab 01. Concepts: JSON Schema, and the fact that the model sees only what you put in the tool definition.

## Estimated time

45 to 60 minutes

## Background

The agent-computer interface is to an agent what a user interface is to a person, and it deserves the same attention. Teams routinely spend days on the wording of a prompt and minutes on the wording of a tool description, even though the description is what decides whether the tool gets called at all.

The model sees exactly three things about a tool: its name, its description, and its input schema. It cannot read your implementation, your docstrings, or your intentions. Everything the model needs in order to choose correctly has to be inside those three fields.

The most valuable sentence in a description is usually the one that says when to call it, not what it does. `Look up current stock` states a capability. `Call this whenever the user asks whether something is available or in stock; the documents do not contain stock levels` states a trigger, and trigger conditions measurably raise the rate of correct calls.

Schemas should make the wrong call hard to express. Use enums instead of free strings for closed sets, require the fields you actually need, and prefer an absolute identifier over something the model must construct by concatenation. A parameter that can only be filled in correctly is worth more than a paragraph of instruction.

Error messages are prompts. When a tool fails, the text you return is the next thing the model reads, so it should name what went wrong and what valid input looks like. Returning `Error: invalid input` teaches nothing; returning `Unknown SKU 'SKU-999'. Known SKUs are SKU-100, SKU-200, SKU-300` lets the model fix its own call on the next turn.

All of this is measurable. Hold a set of questions fixed, vary only the tool description, and count how often the right tool is chosen. That experiment is the point of this lab, and it turns tool wording from a matter of taste into a number.

## Steps

1. Write `GOOD_TOOL` and `VAGUE_TOOL`: the same underlying capability, one with a trigger-condition description and a constrained schema, one with a bare description and a loose schema.
2. Implement `select_tool`: make one model call with a given tool set and return the name of the tool it chose, or None if it answered directly.
3. Implement `selection_rate`: run `select_tool` over a fixed question set and return the fraction where the expected tool was chosen.
4. Implement `compare_descriptions`: run the same questions against both tool variants and return both rates side by side. This is the experiment.
5. Implement `format_tool_error`: turn a failure into a message that names the problem and lists valid inputs, and use it in the tool implementation.
6. Write down which specific edit to the vague description recovered the most selection rate. That observation transfers to every tool you write afterwards.

## Verification

```bash
pytest labs/track-2-tools-context/07-tool-design-aci/tests -v
```

Schema validity and error formatting are checked offline. Passing means both tool definitions are structurally valid, the error message names the valid options rather than just reporting failure, and the selection-rate arithmetic is correct. The comparison itself needs an API key and skips without one.

## Going further

- Add a third tool whose purpose overlaps with the first and measure how much selection accuracy drops. Overlapping tools are a common and avoidable failure.
- Rename `get_stock_level` to `gsl` with the description unchanged and re-measure. Names carry more weight than most people expect.
- Have the tool return a deliberately unhelpful error and count how many extra turns the model needs to recover.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Agent-computer interface design: tool schemas, naming, descriptions, and error design.
- **Databricks Generative AI Engineer Associate**: Tool and agent frameworks; evaluation and monitoring.
- **NVIDIA NCA Generative AI LLMs**: Prompt engineering; software development; experimentation.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
