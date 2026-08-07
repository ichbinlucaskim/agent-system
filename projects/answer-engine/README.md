# Answer engine

A worked example of [system-design case 02](../../system-design/02-answer-engine/README.md):
a **read-only answer pipeline** where the costly failure is a fluent answer that
outruns its evidence, not a wrong side effect.

Strictly speaking this is a **pure workflow**, not an agent. Every stage is
predetermined code. The model only writes the final answer, and only after
citations are already embedded in the prompt. Compare with
`projects/support-desk` (case 06), which opens a bounded agent loop on the
account-changing branch.

## Pipeline

```text
                         packaging (CLI / HTTP)
                                   |
                                   v
                              question
                                   |
                                   v
                         +------------------+
                         | intent parse     |   workflow
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         | hybrid retrieval |   workflow
                         | keyword + dense  |
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         | staged rerank    |   workflow
                         | careful score    |
                         | quality bar      |
                         | fail-safe restart|
                         +--------+---------+
                                  |
                     enough evidence? ------no----> abstain
                                  |
                                 yes
                                  v
                         +------------------+
                         | prompt assembly  |   workflow
                         | citations BEFORE |
                         | generation       |
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         | constrained      |   model writes here only
                         | synthesis        |
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         | evaluation       |   workflow
                         | docs + citations |
                         +------------------+
```

| Segment | Kind | Role |
| --- | --- | --- |
| Intent | workflow | Cheap bias for retrieval; errors propagate (no later verify loop) |
| Hybrid retrieval | workflow | Keyword + dense shortlist (lab 08/09) |
| Staged rerank | workflow | Careful score on few candidates; threshold + one restart |
| Cite-before-gen | workflow | Attribution is a generation constraint, not a post-hoc patch |
| Synthesis | model step | Answer only from assembled passages |
| Evaluation | workflow | Relevant docs retrieved? Citations present? Abstain when empty? |
| Packaging | workflow | `/health` never calls the model |

No HITL. Action space is read-only, so there is nothing to approve.

## What you can feel here

- Correctness is forced by **grounding**, not by a verification agent after the fact.
- Staging spends the latency budget unevenly: cheap over many, careful over few.
- Out-of-corpus questions must abstain rather than invent.
- Offline mode stitches cited snippets so the suite runs without an API key.

## Setup

```bash
cd projects/answer-engine
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pip install -e ../../agent-lab
cp .env.example .env   # only needed for live ask
```

## Run

```bash
python -c "from answer_engine.evaluation.runner import run_suite_offline; \
import json; print(json.dumps(run_suite_offline(), indent=2))"

pytest -q
python -m answer_engine smoke

python -m answer_engine ask "What is the difference between a workflow and an agent?" --offline
python -m answer_engine ask "When should citations be embedded?" --offline --json
```

## Structure

```text
src/answer_engine/
  intent/        # parse + retrieval query bias
  retrieval/     # corpus, hybrid keyword+dense
  ranking/       # staged rerank, threshold, restart
  synthesis/     # cite-before-gen assembly + answer
  pipeline.py    # wires the fixed workflow
  evaluation/    # grounding/citation suite
  packaging/     # config, CLI, HTTP, smoke
data/corpus/     # small local knowledge base
data/eval/       # labelled questions
```

## Related

- System design: `02-answer-engine`
- Contrast: `projects/support-desk` (case 06 hybrid workflow+agent)
- Labs: 02, 03, 08, 09, 18
- Cloud map: `agent-lab/docs/from-lab-to-cloud.md`
