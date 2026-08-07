"""Lab 15 - Evaluation (reference solution).

An eval turns a prompt change from a guess into a number you can compare.
Deterministic checks catch most regressions for free, a rubric judge covers
what cannot be asserted, and repeated runs turn single-run noise into a pass
rate with the flaky cases named.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from common.client import complete, text_of


@dataclass(frozen=True)
class Check:
    """One deterministic check.

    fn returns None on pass and a human-readable reason on failure, so a
    failing check is a bug report rather than a bare boolean.
    """

    name: str
    fn: Callable[[str], str | None]


@dataclass(frozen=True)
class Case:
    """One evaluation case: an id, an input, and its deterministic checks."""

    id: str
    input: str
    checks: list[Check] = field(default_factory=list)


def run_deterministic(case: Any, output: str) -> dict[str, Any]:
    """Apply every deterministic check and report per-check results."""
    checks: list[dict[str, Any]] = []
    for check in case.checks:
        reason = check.fn(output)
        checks.append(
            {"name": check.name, "passed": reason is None, "reason": reason}
        )
    return {
        "case_id": case.id,
        "passed": all(entry["passed"] for entry in checks),
        "checks": checks,
    }


JUDGE_SYSTEM = (
    "You are grading one output of another system against a rubric. Score "
    "the output on its own merits; do not reward confident phrasing.\n\n"
    "Reply with a single JSON object and nothing else:\n"
    '{"score": <integer 1 to 5>, "reason": "<one sentence>"}'
)


def parse_judgement(reply: str) -> dict[str, Any]:
    """Parse a judge reply into {'score', 'reason'} or {'error', 'raw'}.

    A reply that does not parse is an error, never a score of zero. Folding
    parse failures into the metric would let judge bugs masquerade as
    regressions in the system under test.
    """
    start, end = reply.find("{"), reply.rfind("}")
    if start == -1 or end <= start:
        return {"error": "no JSON object in judge reply", "raw": reply}
    try:
        payload = json.loads(reply[start : end + 1])
    except json.JSONDecodeError as exc:
        return {"error": f"judge reply is not valid JSON: {exc}", "raw": reply}
    score = payload.get("score")
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return {"error": "judge reply has no numeric score", "raw": reply}
    return {"score": float(score), "reason": str(payload.get("reason", ""))}


def judge(case: Any, output: str, rubric: str) -> dict[str, Any]:
    """Score an output against a rubric using a model call."""
    prompt = (
        f"Rubric:\n{rubric}\n\n"
        f"Input given to the system:\n{case.input}\n\n"
        f"Output to grade:\n{output}"
    )
    response = complete([{"role": "user", "content": prompt}], system=JUDGE_SYSTEM)
    return parse_judgement(text_of(response))


def default_target(question: str) -> str:
    """The system under test: one plain model call."""
    response = complete([{"role": "user", "content": question}])
    return text_of(response)


def run_suite(
    cases: list[Any],
    *,
    runs: int = 3,
    rubric: str | None = None,
    target: Callable[[str], str] | None = None,
    judge_fn: Callable[[Any, str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run every case several times and collect the results.

    target produces the system-under-test output for one input and defaults
    to a live model call; pass a stub to exercise the machinery offline. The
    raw outputs are kept so one failure can be diagnosed without a re-run.

    The pass rate is deterministic only. Judge scores are collected alongside
    as a parallel signal; folding them into the rate would mix two different
    kinds of variance into one number.
    """
    target = default_target if target is None else target
    judge_fn = judge if judge_fn is None else judge_fn

    by_case: dict[str, Any] = {}
    for case in cases:
        records: list[dict[str, Any]] = []
        passes = 0
        for _ in range(runs):
            output = target(case.input)
            deterministic = run_deterministic(case, output)
            record: dict[str, Any] = {
                "output": output,
                "deterministic": deterministic,
            }
            if rubric is not None:
                record["judgement"] = judge_fn(case, output, rubric)
            if deterministic["passed"]:
                passes += 1
            records.append(record)
        # The pass rate is over all runs, never the last run's verdict.
        by_case[case.id] = {
            "pass_rate": passes / runs if runs else 0.0,
            "runs": records,
        }
    return {"runs": runs, "cases": by_case}


def _status(pass_rate: float) -> str:
    if pass_rate == 1.0:
        return "pass"
    if pass_rate == 0.0:
        return "fail"
    # Strictly between 0 and 1: neither reliable nor broken. Hiding these
    # behind an aggregate hides exactly the cases most worth reading.
    return "flaky"


def format_report(results: dict[str, Any]) -> str:
    """Render pass rates, flaky cases, and failures as text."""
    runs = results["runs"]
    lines = [f"suite: {len(results['cases'])} cases x {runs} runs"]
    header = f"{'case':<24}{'pass rate':>10}  status"
    lines += [header, "-" * len(header)]

    failures: list[str] = []
    errors: list[str] = []
    for case_id, entry in results["cases"].items():
        rate = entry["pass_rate"]
        lines.append(f"{case_id:<24}{rate:>10.2f}  {_status(rate)}")
        for index, record in enumerate(entry["runs"], start=1):
            for check in record["deterministic"]["checks"]:
                if not check["passed"]:
                    failures.append(
                        f"  {case_id} run {index} [{check['name']}]: "
                        f"{check['reason']}\n"
                        f"    output: {record['output']}"
                    )
            judgement = record.get("judgement")
            if judgement and "error" in judgement:
                errors.append(f"  {case_id} run {index}: {judgement['error']}")

    if failures:
        lines += ["", "failures:"] + failures
    if errors:
        lines += ["", "judge errors:"] + errors
    return "\n".join(lines)


def _scripted_target(script: dict[str, list[str]]) -> Callable[[str], str]:
    """A stub system whose outputs cycle per input, to demo the suite offline."""
    counts: dict[str, int] = {}

    def target(question: str) -> str:
        outputs = script[question]
        index = counts.get(question, 0)
        counts[question] = index + 1
        return outputs[index % len(outputs)]

    return target


def _contains(needle: str) -> Callable[[str], str | None]:
    def check(output: str) -> str | None:
        if needle.lower() in output.lower():
            return None
        return f"expected the output to mention {needle!r}"

    return check


def _max_chars(limit: int) -> Callable[[str], str | None]:
    def check(output: str) -> str | None:
        if len(output) <= limit:
            return None
        return f"output is {len(output)} characters, the limit is {limit}"

    return check


def main() -> int:
    """Run a small suite twice and compare the reports.

    The target is scripted so the suite machinery is visible without an API
    key. The second run changes one behaviour (the shipping phrasing) and
    reprints the report: that before/after comparison is the point of the lab.
    Swap _scripted_target for default_target to evaluate a real system.
    """
    returns_q = "How long do I have to return an item?"
    weather_q = "What is the weather in Busan today?"
    shipping_q = "How fast is standard shipping?"

    cases = [
        Case(
            "returns-window",
            returns_q,
            [Check("mentions 30 days", _contains("30 days"))],
        ),
        Case(
            "weather-refusal",
            weather_q,
            [Check("refuses out of scope", _contains("do not know"))],
        ),
        Case(
            "shipping-brief",
            shipping_q,
            [
                Check("mentions 3 to 5 days", _contains("3 to 5")),
                Check("stays short", _max_chars(120)),
            ],
        ),
    ]

    before_script = {
        # Passes every run.
        returns_q: ["Returns are accepted within 30 days of delivery."],
        # Fails every run: the scripted system answers instead of refusing.
        weather_q: ["It is sunny in Busan."],
        # Flaky: one phrasing in three drops the concrete number.
        shipping_q: [
            "Standard shipping takes 3 to 5 business days.",
            "Standard shipping takes 3 to 5 business days.",
            "Standard shipping is usually fairly quick.",
        ],
    }
    # One deliberate change: shipping always cites the number. Everything
    # else is identical so the report delta is attributable.
    after_script = {
        **before_script,
        shipping_q: [
            "Standard shipping takes 3 to 5 business days.",
            "Standard shipping takes 3 to 5 business days.",
            "Standard shipping takes 3 to 5 business days.",
        ],
    }

    print("=== before (shipping phrasing flaky) ===")
    print(format_report(run_suite(cases, runs=3, target=_scripted_target(before_script))))
    print()
    print("=== after (shipping always cites 3 to 5) ===")
    print(format_report(run_suite(cases, runs=3, target=_scripted_target(after_script))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
