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

The experiment needs a competing tool. With only one tool there is no selection to make: the model calls it for anything vaguely related, and a one-word description scores a perfect rate, as does a mangled name. Put a second tool beside it and the failure appears, usually as the opposite of what people expect. The damage a vague description does is not that the tool goes uncalled, it is that the tool gets called for everything. `Look up stock` never says what the tool is not for, so questions about materials and cleaning get pulled into it too. That is why the sentence drawing a boundary is worth so much.

A schema is documentation as well as constraint. The model reads enum values and field descriptions as evidence about what a tool is for, so tightening the schema lifts the selection rate and not only the argument quality. In this lab's measurements, fixing the wording and fixing the schema contributed about equally.

## Steps

1. Write the tool definitions: `DOCS_TOOL` for the stock tool to compete with, and four variants of the stock tool that share one name. `GOOD_TOOL` has a trigger-condition description and a constrained schema, `VAGUE_TOOL` has a bare description and a loose schema, and `TRIGGER_ONLY_TOOL` and `SCHEMA_ONLY_TOOL` each change one field so the two contributions can be read apart. Fill `CASES` with questions that sit on the boundary between the two tools.
2. Implement `select_tool`: make one model call with a given tool set and return the name of the tool it chose, or None if it answered directly.
3. Implement `selection_rate`: run `select_tool` over a fixed question set and return the fraction where the expected tool was chosen. The cases are independent, so run them concurrently the way lab 04 did.
4. Implement `compare_descriptions`: hold the questions and the competing tool fixed, vary only the stock tool, and return all four rates side by side. This is the experiment.
5. Implement `format_tool_error`: turn a failure into a message that names the problem and lists valid inputs, and use it in the tool implementation.
6. Write down which specific edit recovered the most selection rate. Subtracting the four rates gives the share belonging to the wording and the share belonging to the schema. That observation transfers to every tool you write afterwards.

## Verification

```bash
pytest labs/track-2-tools-context/07-tool-design-aci/tests -v
```

Schema validity and error formatting are checked offline. Passing means every tool definition is structurally valid, the middle variants differ in exactly one field each, the case set really puts the two tools in competition, the error message names the valid options rather than just reporting failure, and the selection-rate arithmetic is correct. The comparison itself needs an API key and skips without one.

## Going further

- Add a third tool whose purpose overlaps with the first and measure how much selection accuracy drops. Overlapping tools are a common and avoidable failure.
- Rename `get_stock_level` to `gsl` with the description unchanged and re-measure. Keep the competing tool exposed while you do: with a single tool on offer, mangling the name costs nothing.
- Have the tool return a deliberately unhelpful error and count how many extra turns the model needs to recover.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Agent-computer interface design: tool schemas, naming, descriptions, and error design.
- **Databricks Generative AI Engineer Associate**: Tool and agent frameworks; evaluation and monitoring.
- **NVIDIA NCA Generative AI LLMs**: Prompt engineering; software development; experimentation.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
