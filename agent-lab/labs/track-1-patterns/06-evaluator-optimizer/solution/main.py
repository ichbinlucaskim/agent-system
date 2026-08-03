"""Lab 06 - Evaluator and optimizer (reference solution).

A generator produces a draft, an evaluator scores it against explicit
criteria, and the critique is threaded into the next generation. The loop
has two exits, success and budget, and it returns the best draft seen
because scores do not increase monotonically.
"""

from __future__ import annotations

import json
from typing import Any

from common.client import complete, text_of

# Criteria specific enough to grade independently. Asking whether a draft is
# 'good' yields noise; each line here is a check the evaluator can pass or
# fail on its own.
CRITERIA: list[str] = [
    "Mentions every feature named in the task and invents no new ones.",
    "Stays under 150 words.",
    "Opens with a single-sentence summary of what the product does.",
    "Uses the active voice throughout.",
    "Ends with one concrete call to action.",
]


def _criteria_block() -> str:
    """Render CRITERIA as a numbered block for prompts."""
    return "\n".join(
        f"{index}. {criterion}" for index, criterion in enumerate(CRITERIA, 1)
    )


def generate(task: str, feedback: str | None = None) -> str:
    """Produce a draft, optionally guided by the previous critique."""
    system = (
        "You write short product announcements. Satisfy every one of these "
        f"criteria:\n{_criteria_block()}"
    )
    content = task
    if feedback:
        # The critique goes in as an explicit instruction. If the second
        # call cannot see it, the loop is resampling, not refining.
        content = (
            f"{task}\n\nA reviewer critiqued the previous draft. Fix every "
            f"point below without breaking the criteria:\n{feedback}"
        )
    response = complete([{"role": "user", "content": content}], system=system)
    return text_of(response)


def evaluate(task: str, draft: str) -> dict[str, Any]:
    """Score a draft against CRITERIA and explain what is wrong."""
    system = (
        "You are a strict reviewer. Grade the draft against each criterion:\n"
        f"{_criteria_block()}\n\n"
        "Score 0 to 10 overall, where 10 means every criterion is met. "
        "Respond with JSON only, no prose and no code fences: "
        '{"score": <int>, "passed": <bool>, "feedback": "<the specific '
        'fixes needed, one per failed criterion>"}'
    )
    prompt = f"Task: {task}\n\nDraft:\n{draft}"
    response = complete([{"role": "user", "content": prompt}], system=system)
    raw = text_of(response)
    # Parse the JSON rather than reading a number out of prose. An evaluator
    # whose output needs interpretation is an evaluator you cannot loop on.
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"evaluator did not return JSON: {raw[:120]!r}")
    parsed = json.loads(raw[start : end + 1])
    return {
        "score": int(parsed.get("score", 0)),
        "passed": bool(parsed.get("passed", False)),
        "feedback": str(parsed.get("feedback", "")),
    }


def is_done(
    evaluation: dict[str, Any],
    iteration: int,
    *,
    max_iterations: int,
    target_score: int,
) -> tuple[bool, str]:
    """Decide whether the loop should stop, and say why."""
    score = evaluation["score"]
    if score >= target_score:
        return (True, f"success: score {score} reached target {target_score}")
    if iteration >= max_iterations:
        # The unconditional exit. Without it, a task the model cannot
        # satisfy consumes tokens until something else breaks.
        return (
            True,
            f"budget exhausted: {max_iterations} iterations without "
            f"reaching {target_score}",
        )
    return (False, f"score {score} below target {target_score}, continuing")


def refine(
    task: str, *, max_iterations: int = 3, target_score: int = 8
) -> dict[str, Any]:
    """Run the generate and evaluate loop under a fixed budget."""
    history: list[dict[str, Any]] = []
    best_draft, best_score, best_iteration = "", -1, 0
    feedback: str | None = None
    stop_reason = "no iterations ran"

    for iteration in range(1, max_iterations + 1):
        draft = generate(task, feedback)
        evaluation = evaluate(task, draft)
        history.append(
            {
                "iteration": iteration,
                "score": evaluation["score"],
                "feedback": evaluation["feedback"],
            }
        )
        # Track the best draft, not the latest. A third iteration can score
        # below the second, and the caller deserves the peak, not the tail.
        if evaluation["score"] > best_score:
            best_draft = draft
            best_score = evaluation["score"]
            best_iteration = iteration

        done, stop_reason = is_done(
            evaluation,
            iteration,
            max_iterations=max_iterations,
            target_score=target_score,
        )
        if done:
            break
        feedback = evaluation["feedback"]

    return {
        "draft": best_draft,
        "score": best_score,
        "iteration": best_iteration,
        "stop_reason": stop_reason,
        "history": history,
    }


def main() -> int:
    """Refine one announcement and print the score history."""
    task = (
        "Announce our new reusable water bottle: keeps drinks cold for 24 "
        "hours, made from recycled steel, ships in plastic-free packaging."
    )
    outcome = refine(task)

    print("score history:")
    for entry in outcome["history"]:
        print(f"  iteration {entry['iteration']}: score {entry['score']}")
    print(f"stop reason: {outcome['stop_reason']}")
    print(
        f"\nbest draft (iteration {outcome['iteration']}, "
        f"score {outcome['score']}):\n{outcome['draft']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
