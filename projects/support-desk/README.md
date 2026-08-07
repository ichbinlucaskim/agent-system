# Support desk

A worked example of [system-design case 06](../../system-design/06-tool-agent-user-support/README.md):
a **tool-agent-user** support desk where the costly failure is a wrong *action*,
not a wrong answer.

Strictly speaking this is not a pure agent. It is a **workflow that opens a
bounded agent loop only on the account-changing branch**. Routing, the FAQ
path, HITL, tool preconditions, eval, and packaging are predetermined code.
Only inside `agent/loop.py` does the model choose the next tool.

This is a runnable mini-product for practical intuition after the agent-lab
course.

## Pipeline

```text
                         packaging (CLI / HTTP)
                                   |
                                   v
                         +------------------+
                         | input guardrail  |   workflow
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         | route()          |   workflow
                         | FAQ | account    |
                         +---+------+-------+
                             |      |
              workflow       |      |      agent segment
              +--------------v      v------------------+
              |  FAQ path           account path       |
              |  retrieve policy    while budget left: |
              |  one model call     model + tools      |
              |  no side-effect     |                  |
              |  tools              v                  |
              |               tools_gate               |
              |               auto | confirm | forbid  |
              |               tool preconditions       |
              |               SQLite account state     |
              +--------------+------+------------------+
                             |      |
                             v      v
                         +------------------+
                         | evaluation       |   workflow
                         | audits + DB      |   (oracle = actions)
                         +------------------+
```

| Segment | Kind | What decides the next step |
| --- | --- | --- |
| Input guardrail | workflow | Code (`check_input`) |
| `route()` | workflow | Code (keywords / order id) |
| FAQ path | workflow | Fixed retrieve then one completion |
| Account path | **agent** | Model picks tools inside the loop |
| `tools_gate` | workflow fence | HITL map + tool preconditions (model cannot override) |
| Budgets / `stop_reason` | workflow fence | Code ceilings around the agent |
| Evaluation | workflow | Deterministic checks on audits and DB |
| Packaging | workflow | Adapters; `/health` never calls the model |

See also system-design case 07 (`workflow-not-agent`): the account branch could
be a pure state machine. This project keeps a loop there because the dialogue
is open-ended, which is the case 06 assumption.

## What you can feel here

- Policy markdown is retrieved for reference. Permission is compiled into tool
  preconditions and the HITL map. Those are different layers.
- Account state lives in SQLite and is re-read through tools, not cached in chat.
- FAQ never exposes refund or cancel tools. Routing chooses capability.
- Eval scores whether the right tools succeeded, not how polished the reply was.
- Smoke and `/health` prove process liveness without a model call.

## Setup

```bash
cd projects/support-desk
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pip install -e ../../agent-lab   # if common is not importable
cp .env.example .env             # set ANTHROPIC_API_KEY for live ask
```

## Run

```bash
python -c "from support_desk.evaluation.runner import run_suite_offline; \
import json; print(json.dumps(run_suite_offline(), indent=2))"

pytest -q
python -m support_desk smoke

python -m support_desk ask "How many days do I have to return an item?" --report
python -m support_desk ask "Refund ORD-100 in full." --approve --report

python -m support_desk.packaging.mcp_order_server
```

## Seed world

| Order | Status | Notes |
| --- | --- | --- |
| ORD-100 | delivered, 5 days ago, $49.99 | refundable |
| ORD-200 | delivered, 45 days ago, $120 | window expired |
| ORD-300 | shipped, $80 | cancel forbidden |
| ORD-400 | processing, $25 | cancellable |

## Structure

Folders follow the pipeline layers. Most of them are workflow. Only `agent/`
is the agent segment.

```text
src/support_desk/
  packaging/      # adapters: config, CLI, HTTP, smoke, MCP
  routing/        # workflow: FAQ vs account
  tools_gate/     # workflow fence: tools, HITL, DB, policy RAG, guardrails
  agent/          # agent segment: loop.py (budgets, stop_reason)
  evaluation/     # workflow: action-level suite + reports
  paths.py
tests/
  packaging/  routing/  tools_gate/  evaluation/
data/
  policy/     # written policy corpus (reference, not permission)
  seed.sql
  eval/       # cases scored on actions and DB state
```

## Related

- System design: `06-tool-agent-user-support`, and `07-workflow-not-agent`
- Labs: 03, 07, 08, 10, 12, 14, 15, 16, 17, 18
- Cloud map: `agent-lab/docs/from-lab-to-cloud.md`
