"""Lab 05 - Orchestrator and workers (reference solution).

The lead call reads the task and decides what the subtasks are, workers
execute them with narrow context, and the lead synthesizes the results. The
subtasks are not known in advance, which is the whole difference from
sectioning, and it is why the generated plan is treated as untrusted input.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from common.client import complete, text_of


def _parse_json_array(raw: str) -> list[Any]:
    """Pull the first JSON array out of a model response, or fail loudly."""
    start, end = raw.find("["), raw.rfind("]")
    if start == -1 or end <= start:
        raise ValueError(f"planner did not return a JSON array: {raw[:120]!r}")
    try:
        parsed = json.loads(raw[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError(f"planner returned unparseable JSON: {exc}") from exc
    if not isinstance(parsed, list):
        raise ValueError("planner JSON parsed but was not a list")
    return parsed


# Asking for "independent" subtasks is not enough on its own. Left at that,
# the planner regularly spends its last slot on a "synthesize the other
# subtasks" entry, which runs concurrently with the very subtasks it claims
# to read and so has nothing to work from. validate_plan cannot catch it:
# the entry has an id, a description, and no duplicate, so its shape is
# perfect and only its meaning is wrong. Shape is all validation can see,
# which is why the boundary has to be spelled out to the planner instead.
PLAN_RULES = (
    "Every subtask must be answerable on its own, with no access to any "
    "other subtask's output.",
    "Never emit a subtask that summarizes, combines, or builds on the "
    "other subtasks. Synthesis is the lead's job and happens after the "
    "workers have finished.",
    "Every id must be unique.",
)


def plan(task: str) -> list[dict[str, Any]]:
    """Lead call that decomposes a task into subtasks as structured data."""
    rules = " ".join(
        f"({number}) {rule}" for number, rule in enumerate(PLAN_RULES, start=1)
    )
    system = (
        "You are the lead of a small research team. Decompose the task into "
        "independent subtasks that can run in any order. Respond with a JSON "
        "array only, no prose and no code fences, in this shape: "
        '[{"id": "t1", "description": "one specific subtask"}]. '
        f"Use between two and six subtasks. Rules: {rules}"
    )
    response = complete([{"role": "user", "content": task}], system=system)
    # Parse, never string-match. A plan we cannot parse is a plan we cannot
    # validate, and the only safe response to that is a loud failure.
    return _parse_json_array(text_of(response))


def validate_plan(
    subtasks: list[dict[str, Any]], *, max_subtasks: int = 6
) -> list[dict[str, Any]]:
    """Reject malformed entries, drop duplicates, and cap the count."""
    valid: list[dict[str, Any]] = []
    seen_descriptions: set[str] = set()
    seen_ids: set[str] = set()
    for entry in subtasks:
        if not isinstance(entry, dict):
            continue
        subtask_id = entry.get("id")
        description = entry.get("description")
        if not isinstance(subtask_id, str) or not subtask_id.strip():
            continue
        if not isinstance(description, str) or not description.strip():
            continue
        subtask_id = subtask_id.strip()
        # Everything downstream addresses a subtask by its id: results are
        # looked up by it and synthesis labels each finding with it. A
        # repeated id makes two subtasks indistinguishable, so the second
        # one goes rather than silently shadowing the first.
        if subtask_id in seen_ids:
            continue
        # Duplicate descriptions collapse to one entry: the same work should
        # not be paid for twice just because the planner repeated itself.
        key = " ".join(description.lower().split())
        if key in seen_descriptions:
            continue
        seen_ids.add(subtask_id)
        seen_descriptions.add(key)
        valid.append({"id": subtask_id, "description": description.strip()})
    # The cap bounds cost no matter how enthusiastic the generated plan was.
    return valid[:max_subtasks]


def run_worker(subtask: dict[str, Any], context: str) -> dict[str, Any]:
    """Execute one subtask with a narrow prompt and narrow context."""
    system = (
        "You are one worker on a team. Complete only the subtask you are "
        "given, using only the context provided. Be brief, concrete, and "
        "factual. Do not attempt the other subtasks."
    )
    prompt = f"Subtask: {subtask['description']}\n\nContext:\n{context}"
    try:
        response = complete([{"role": "user", "content": prompt}], system=system)
        return {"id": subtask["id"], "result": text_of(response), "error": None}
    except Exception as exc:
        # A worker failure is data for synthesis, not an exception for the
        # run. The other workers' output is still worth synthesizing.
        return {
            "id": subtask["id"],
            "result": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def synthesize(task: str, results: list[dict[str, Any]]) -> str:
    """Final lead call that answers the original task from worker output."""
    blocks: list[str] = []
    for entry in results:
        if entry.get("error"):
            blocks.append(f"[{entry['id']}] FAILED: {entry['error']}")
        else:
            blocks.append(f"[{entry['id']}] {entry['result']}")
    findings = "\n\n".join(blocks) if blocks else "(no worker output)"
    system = (
        "You are the lead of a team. Answer the original task using the "
        "worker findings below. Resolve contradictions between workers, "
        "drop anything irrelevant, and note explicitly when a failed "
        "subtask leaves a gap in the answer. Write a coherent answer, not "
        "a list of the findings."
    )
    prompt = f"Original task: {task}\n\nWorker findings:\n{findings}"
    response = complete([{"role": "user", "content": prompt}], system=system)
    return text_of(response)


def orchestrate(
    task: str, *, max_workers: int = 4, max_subtasks: int = 6
) -> dict[str, Any]:
    """Plan, validate, run workers concurrently, and synthesize."""
    subtasks = validate_plan(plan(task), max_subtasks=max_subtasks)

    results: list[dict[str, Any]] = []
    if subtasks:
        workers = min(max_workers, len(subtasks))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [
                pool.submit(run_worker, subtask, task) for subtask in subtasks
            ]
            results = [future.result() for future in futures]

    if results:
        answer = synthesize(task, results)
    else:
        answer = "The planner produced no usable subtasks, so nothing ran."

    # The plan rides along with the answer: an orchestrated run is expensive,
    # and the plan is what makes the bill explainable afterwards.
    return {"plan": subtasks, "results": results, "answer": answer}


def main() -> int:
    """Orchestrate one open-ended task and show the plan beside the answer."""
    task = (
        "Our small online store wants to start selling in the EU. Summarize "
        "what we need to think about across shipping, taxes, and returns."
    )
    outcome = orchestrate(task)

    print(f"plan ({len(outcome['plan'])} subtasks):")
    for subtask in outcome["plan"]:
        print(f"  [{subtask['id']}] {subtask['description']}")
    print()
    for entry in outcome["results"]:
        status = "failed" if entry.get("error") else "ok"
        print(f"worker {entry['id']}: {status}")
    print(f"\nanswer:\n{outcome['answer']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
