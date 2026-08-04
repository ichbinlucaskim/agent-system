# Lab 01 - The augmented LLM

## Goal

After this lab you can build the base building block that every later lab reuses: a model call augmented with retrieval, tools, and memory, including the tool-use loop that drives it.

## Prerequisites

Lab 00. Concepts: the Messages API request and response shape, content blocks, and the system prompt.

## Estimated time

30 to 45 minutes

## Background

In Anthropic's Building Effective Agents, the augmented LLM is the base building block. Every workflow later in this course, and every agent, is composed of calls of this shape. Getting it right once means the rest of the course is composition rather than reinvention.

Retrieval puts facts into the prompt that the model does not have. Label each retrieved passage with its source id so the answer can cite it and so a reader can tell which claims are grounded. Retrieval that pads the context with irrelevant text is worse than no retrieval: it costs tokens and invites the model to use what it was given.

Tools are actions described by a schema. The model never executes anything. It emits a `tool_use` block naming a tool and its arguments; your code runs the action and sends back a `tool_result`. That split is the whole security boundary, and it is why lab 14 can put an approval gate in the middle of it.

Retrieval and tools answer different questions. A document holds what was true when it was written. A tool reads what is true now. Stock levels, account balances, and today's date belong behind a tool, and the tool description should say so explicitly, because the model will otherwise answer from the documents.

The API is stateless, so memory is simply the history you choose to resend. That makes memory a budget rather than an archive: this lab trims to a fixed number of turns, and lab 11 replaces trimming with compaction.

The loop is driven by `stop_reason`. While it equals `tool_use`, run every `tool_use` block in the response and return all the results in a single user message, one `tool_result` per `tool_use` id. Splitting results across messages or dropping one is a protocol error. Bound the loop with a maximum number of rounds so a confused model cannot spin forever.

## Steps

1. Implement `tokenize` and `retrieve`. Score each document by token overlap with the query, drop documents that share nothing, and return the top k in a deterministic order.
2. Implement `build_system`. State the rules, then list each retrieved document as `[id] text`. Tell the model to cite ids and to say it does not know when nothing supports an answer.
3. Implement `Memory.add` and `Memory.messages`. Keep only the most recent `max_turns` entries, and return a copy so callers cannot mutate the memory by editing the list they got.
4. Implement `run_tool`. Look the SKU up in `INVENTORY`. Return errors as `(text, True)` rather than raising, and make the error name the valid options so the model can recover on the next turn.
5. Implement `augmented_call`. Retrieve, build the system prompt, record the question, then loop: call the model, append its content, and while `stop_reason` is `tool_use` run every block and return all results in one user message. Record the answer in memory and return it.
6. Implement `main`. Ask one question the corpus answers and one stock question that only the tool can answer, using a shared `Memory`.

## Verification

```bash
pytest labs/track-1-patterns/01-augmented-llm/tests -v
```

Retrieval, memory, and tool dispatch are deterministic, so their tests run offline and must pass with no API key. The two end-to-end tests skip without a key. Passing them means the model answered the policy question from the retrieved document and reached for the tool on the stock question rather than guessing.

## Going further

- Weaken the `get_stock_level` description to just `Get stock.` and re-run the stock question. Lab 07 turns this observation into a measurement.
- Add a second tool that overlaps with the first and see which one the model picks.
- Replace token-overlap retrieval with the vector store from lab 08 and compare which documents come back for the same questions.
- Run `main` and read the second answer closely. If the model retracts something it said in the first answer, check what retrieval returned for the second question. The system prompt is rebuilt from the current question every call while memory accumulates, so an earlier answer can outlive the document that grounded it. Lab 11 is where that gets fixed.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: The augmented LLM building block; tool use as an agent-computer interface.
- **Databricks Generative AI Engineer Associate**: Application development including RAG and LLM chains; tool and agent frameworks.
- **NVIDIA NCA Generative AI LLMs**: LLM integration and deployment; prompt engineering.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
