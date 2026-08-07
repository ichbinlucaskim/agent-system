# Repository conventions

This file is the contract for future Claude Code sessions working in this
repository. Read it before adding or changing anything.

## What this repository is

A hands-on lab course for learning agent systems. Nineteen labs, numbered 00
through 18, grouped into four tracks. Learners read a README, fill in the TODOs
in `starter/main.py`, and check their work with pytest. `solution/main.py` is
the reference answer.

## Directory layout

```
lab/
├── common/     shared helpers imported by labs: client, tracing, cost, vectorstore
├── labs/       the nineteen labs, grouped by track
└── docs/       glossary, certification mapping, reading list
```

- `common/` holds anything more than one lab needs. If two labs would copy the
  same helper, it belongs here instead.
- `labs/` subdirectories are `00-setup` and then `track-N-name/NN-lab-name`.
- Nothing outside `common/` is importable as a package. Lab code is loaded by
  path in tests, because directory names start with digits.

## Every lab keeps the fixed folder layout

No exceptions, including new labs:

```
<lab>/
├── README.md          English, primary
├── README.ko.md       Korean mirror
├── starter/main.py    signatures plus TODO comments, no logic
├── solution/main.py   reference implementation
├── tests/test_<slug>.py
└── data/.gitkeep
```

Do not add extra top-level files inside a lab. If a lab needs fixtures, they go
in `data/`. If it needs a helper that other labs would want, it goes in
`common/`.

## The two READMEs must stay in sync

`README.md` is the source of truth and `README.ko.md` is a faithful
translation. **Editing one requires editing the other in the same change.** A
commit that touches only one of the pair is incomplete.

Both files carry the same nine sections in the same order:

1. Title `Lab NN - <Name>`
2. `## Goal`
3. `## Prerequisites`
4. `## Estimated time`
5. `## Background`
6. `## Steps`
7. `## Verification`
8. `## Going further`
9. `## Certification mapping`

In the Korean file, keep technical terms in English (agent, tool use, routing,
orchestrator, retrieval, context window, guardrail, and so on). Do not invent
Korean coinages for them. Code blocks and commands stay byte-identical between
the two files.

The same rule applies to `README.md` / `README.ko.md` at the repository root,
and to `docs/glossary.md` / `docs/glossary.ko.md`.

## Dependencies

The runtime dependency allowlist is exactly three packages:

- `anthropic`
- `pytest`
- `numpy`

Everything else comes from the Python standard library. Do not add LangChain,
LlamaIndex, FAISS, ChromaDB, a cloud SDK, an HTTP framework, or a plotting
library. If a lab seems to need one, it is a sign the lab should teach the
underlying mechanism instead.

`ruff` is optional tooling, not a dependency. `make lint` skips gracefully when
it is absent.

## No cloud rule

No lab may require a cloud account, a hosted database, or a paid service other
than an Anthropic API key. Vector storage is local: numpy for the math,
`sqlite3` from the standard library for persistence. Embeddings in the labs use
a deterministic local hash-based stub, so no embedding endpoint is needed.

## Style

- Python 3.11 or newer. Use modern syntax: `X | None`, `list[str]`, `match`.
- All code, comments, docstrings, variable names, and test names in English.
  Only `README.ko.md` and `docs/*.ko.md` contain Korean.
- No emoji anywhere, in code or in prose.
- No exclamation marks anywhere.
- Prefer plain functions and dataclasses over class hierarchies.
- Comments explain constraints and reasons, not what the next line does.

## Running tests

Run one lab:

```bash
pytest labs/00-setup/tests -v
make test-lab LAB=labs/00-setup
```

Run everything:

```bash
pytest labs -v
make test
```

Tests must pass without an API key. Anything that needs a live call is guarded
so it **skips** rather than fails when `ANTHROPIC_API_KEY` is absent. Use the
skip helper each test file already defines; do not let a missing key turn into
a red test.

Every lab ships with real tests asserting its solution's behaviour. Anything
deterministic is tested offline, driving the solution through stubbed model
calls where needed; only tests that genuinely need a live call carry the
`requires_api` skip marker.

## Secrets

Never commit an API key. `.env` is git-ignored and must stay that way. The only
committed example is `.env.example`, which contains a placeholder. Read the key
from `ANTHROPIC_API_KEY` through `common/client.py`; do not hardcode it, do not
put it in a system prompt, and do not write it into `data/`.
