"""Lab 04 - Parallelization (reference solution).

Parallelization applies when subtasks do not depend on each other. Sectioning
splits one task into independent parts and runs a call per part; voting runs
the same question several times and treats agreement as evidence. Both turn
a sum of latencies into a maximum of latencies.
"""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from common.client import complete, text_of

# Cap the fan-out. Threads are nearly free here because the work is network
# bound, but every concurrent call still counts against the rate limit.
MAX_CONCURRENT_CALLS = 4


def section(task: str) -> list[dict[str, str]]:
    """Split a task into independent aspects, each with its own instruction."""
    # The split is written in code, not chosen by the model. That is what
    # separates sectioning from the orchestrator pattern in lab 05, and it is
    # why every aspect can be genuinely independent of the others.
    return [
        {
            "name": "correctness",
            "instruction": (
                f"Review the text below for the task: {task}. Check only "
                "factual and logical correctness. List each error you find "
                "with the sentence it appears in. Ignore tone and style."
            ),
        },
        {
            "name": "tone",
            "instruction": (
                f"Review the text below for the task: {task}. Check only "
                "tone: is it professional, consistent, and appropriate for "
                "customers? Quote each passage that misses and say why. "
                "Ignore factual accuracy."
            ),
        },
        {
            "name": "legal-risk",
            "instruction": (
                f"Review the text below for the task: {task}. Check only for "
                "legal risk: unsupported claims, promised outcomes, and "
                "missing disclaimers. Quote each risky passage. Ignore tone "
                "and general accuracy."
            ),
        },
    ]


def _run_one_section(section_spec: dict[str, str], text: str) -> str:
    """Make the single model call for one section."""
    response = complete(
        [{"role": "user", "content": text}], system=section_spec["instruction"]
    )
    return text_of(response)


def run_sections(sections: list[dict[str, str]], text: str) -> list[dict[str, Any]]:
    """Run one call per section concurrently, preserving input order."""
    slots: list[dict[str, Any] | None] = [None] * len(sections)
    workers = min(len(sections), MAX_CONCURRENT_CALLS) or 1
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_run_one_section, section_spec, text): index
            for index, section_spec in enumerate(sections)
        }
        for future in as_completed(futures):
            index = futures[future]
            name = sections[index]["name"]
            try:
                slots[index] = {"name": name, "result": future.result(), "error": None}
            except Exception as exc:
                # One failed call must not cost the whole batch. The error
                # keeps its slot so the merge can say what is missing.
                slots[index] = {
                    "name": name,
                    "result": None,
                    "error": f"{type(exc).__name__}: {exc}",
                }
    # Results were written by index, so the order matches sections, not the
    # order in which the futures happened to complete.
    return [slot for slot in slots if slot is not None]


def merge_sections(results: list[dict[str, Any]]) -> str:
    """Combine section results into one labelled report."""
    blocks: list[str] = []
    for entry in results:
        if entry.get("error"):
            body = f"(this section failed: {entry['error']})"
        else:
            body = str(entry["result"]).strip()
        # Each section keeps its own heading. Blending the findings into one
        # prose blob loses the reason for sectioning in the first place.
        blocks.append(f"== {entry['name']} ==\n{body}")
    return "\n\n".join(blocks)


def normalize_answer(answer: str) -> str:
    """Collapse trivial formatting differences before votes are compared."""
    return " ".join(answer.split()).strip().rstrip(".").lower()


def _ask_once(question: str) -> str:
    """Make one short-answer call for the voting pattern."""
    system = (
        "Answer the question with a single short answer and nothing else. "
        "No explanation, no punctuation beyond the answer itself."
    )
    response = complete([{"role": "user", "content": question}], system=system)
    return text_of(response)


def vote(question: str, n: int = 3) -> list[str]:
    """Run the same question n times concurrently and collect the answers."""
    workers = min(n, MAX_CONCURRENT_CALLS) or 1
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_ask_once, question) for _ in range(n)]
        # Normalising before returning means 'Yes.' and 'yes' agree instead
        # of reading as a split vote.
        return [normalize_answer(future.result()) for future in futures]


def majority(answers: list[str]) -> tuple[str, float]:
    """Return the modal answer and the fraction of votes that agreed."""
    if not answers:
        return ("", 0.0)
    counts = Counter(answers)
    top = max(counts.values())
    # Ties break by first appearance, so the same votes always give the same
    # result regardless of hashing or completion order.
    for answer in answers:
        if counts[answer] == top:
            return (answer, top / len(answers))
    return ("", 0.0)  # unreachable, kept for the type checker


def main() -> int:
    """Run one sectioned review and one vote, and print both."""
    task = "review this product announcement before it ships to customers"
    text = (
        "Introducing the AquaPure filter. It removes 100 percent of all "
        "contaminants forever and will cure hard water problems for good. "
        "Buy now, you would be crazy not to."
    )
    sections_list = section(task)
    results = run_sections(sections_list, text)
    print(merge_sections(results))

    question = "Is the following claim safe to publish: 'removes 100 percent of all contaminants forever'? Answer yes or no."
    answers = vote(question, n=3)
    answer, agreement = majority(answers)
    print(f"\nvotes: {answers}")
    print(f"majority answer: {answer!r} with agreement {agreement:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
