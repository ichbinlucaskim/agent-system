# Agent systems lab

A hands-on lab course for learning how agent systems are actually built. Nineteen
labs across four tracks. You read a short README, fill in the TODOs in
`starter/main.py`, and check your work with pytest.

Everything runs locally. The only account you need is an Anthropic API key, and
the runtime dependencies are exactly three packages: `anthropic`, `pytest`, and
`numpy`. There is no agent framework here on purpose: the point is to build the
mechanisms rather than to configure someone else's.

## Who this is for

Engineers who can write Python and have used an LLM API at least once, and who
want to understand the patterns underneath agent frameworks well enough to
choose between them, debug them, and decide when not to use one at all. It also
maps onto the objectives of two certifications; see `docs/cert-mapping.md`.

When you finish the labs and wonder where AWS or common libraries attach, read
`docs/from-lab-to-cloud.md`. The short version: labs decide what must stay true;
libraries speed up the build; cloud is where the same core runs, stores state,
and gets observed.

## The four tracks

- **Track 1, patterns.** The composable workflow patterns: the augmented LLM,
  prompt chaining, routing, parallelization, orchestrator-workers, and
  evaluator-optimizer.
- **Track 2, tools and context.** What you feed the model and what you let it
  do: tool and interface design, retrieval, retrieval quality, an MCP-style
  server, and context engineering.
- **Track 3, autonomy.** Handing control to the model, and bounding it: the
  agent loop, subagents, and human approval gates.
- **Track 4, production.** What separates a demo from a system: evaluation,
  observability, guardrails, and packaging.

## The labs

| Lab | Name | Track | Estimated time | Core or optional |
| --- | --- | --- | --- | --- |
| 00 | [Setup](labs/00-setup/README.md) | Setup | 20 to 30 minutes | core |
| 01 | [The augmented LLM](labs/track-1-patterns/01-augmented-llm/README.md) | Track 1, patterns | 30 to 45 minutes | core |
| 02 | [Prompt chaining](labs/track-1-patterns/02-prompt-chaining/README.md) | Track 1, patterns | 30 to 45 minutes | core |
| 03 | [Routing](labs/track-1-patterns/03-routing/README.md) | Track 1, patterns | 30 to 45 minutes | core |
| 04 | [Parallelization](labs/track-1-patterns/04-parallelization/README.md) | Track 1, patterns | 45 to 60 minutes | core |
| 05 | [Orchestrator and workers](labs/track-1-patterns/05-orchestrator-workers/README.md) | Track 1, patterns | 45 to 60 minutes | core |
| 06 | [Evaluator and optimizer](labs/track-1-patterns/06-evaluator-optimizer/README.md) | Track 1, patterns | 45 to 60 minutes | core |
| 07 | [Tool design and the agent-computer interface](labs/track-2-tools-context/07-tool-design-aci/README.md) | Track 2, tools and context | 45 to 60 minutes | core |
| 08 | [RAG basics](labs/track-2-tools-context/08-rag-basics/README.md) | Track 2, tools and context | 60 to 90 minutes | core |
| 09 | [Retrieval quality](labs/track-2-tools-context/09-retrieval-quality/README.md) | Track 2, tools and context | 60 to 90 minutes | optional |
| 10 | [An MCP-style server](labs/track-2-tools-context/10-mcp-server/README.md) | Track 2, tools and context | 60 to 90 minutes | core |
| 11 | [Context and memory](labs/track-2-tools-context/11-context-memory/README.md) | Track 2, tools and context | 45 to 60 minutes | core |
| 12 | [The agent loop](labs/track-3-autonomy/12-agent-loop/README.md) | Track 3, autonomy | 60 to 90 minutes | core |
| 13 | [Subagents](labs/track-3-autonomy/13-subagents/README.md) | Track 3, autonomy | 45 to 60 minutes | core |
| 14 | [Human in the loop](labs/track-3-autonomy/14-human-in-the-loop/README.md) | Track 3, autonomy | 45 to 60 minutes | core |
| 15 | [Evaluation](labs/track-4-production/15-evaluation/README.md) | Track 4, production | 60 to 90 minutes | core |
| 16 | [Observability](labs/track-4-production/16-observability/README.md) | Track 4, production | 45 to 60 minutes | optional |
| 17 | [Guardrails](labs/track-4-production/17-guardrails/README.md) | Track 4, production | 45 to 60 minutes | core |
| 18 | [Packaging and deployment](labs/track-4-production/18-packaging-deploy/README.md) | Track 4, production | 45 to 60 minutes | optional |

Labs 09, 16, and 18 are marked optional. They are not less important in
production; they are the ones you can defer while you are still learning the
core mechanisms.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Then put your key in `.env` and export it:

```bash
export $(grep -v '^#' .env | xargs)
```

`.env` is git-ignored. Never commit a real key.

There is also a Makefile target that does the venv and the install:

```bash
make setup
```

## Running tests

```bash
pytest labs -v                      # everything
pytest labs/00-setup/tests -v       # one lab
make test
make test-lab LAB=labs/00-setup
```

Tests are written so that the whole suite passes with no API key set. Anything
that needs a live call skips cleanly instead of failing, so you can work through
the offline parts of a lab before spending anything.

## What is implemented today

All nineteen labs are complete: a fully written README in both languages, a
`starter/main.py` with signatures and TODOs, a reference `solution/main.py`,
and a test file with real assertions against the solution. Everything
deterministic is tested offline; the few tests that need a live model call skip
cleanly without an API key.

The exercise is still yours: work from `starter/main.py` and use the tests to
check your implementation. The solutions are reference answers to compare
against, not the starting point.

## Repository layout

```
agent-lab/
├── common/     shared helpers: client, tracing, cost, vectorstore
├── labs/       the nineteen labs, grouped by track
└── docs/       glossary, certification mapping, reading list,
                lab-to-cloud map
```

`CLAUDE.md` holds the conventions for this repository, including the rule that
`README.md` and `README.ko.md` must be edited together.

## Korean

Korean documentation is in `README.ko.md`. Every lab ships a `README.ko.md`
alongside its `README.md`, and the glossary has a Korean edition at
`docs/glossary.ko.md`.
