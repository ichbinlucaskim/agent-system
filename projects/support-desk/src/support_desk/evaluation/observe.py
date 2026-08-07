"""Turn a Trace into a short cost and latency report (lab 16).

Purpose
    Render a human-readable summary of route, stop reason, answer snippet,
    trace timing/cost text, and HITL audits after a handle_message run.

Why
    This is the observation side of the evaluation layer: operators and lab
    exercises need a terminal-friendly report without exporting full JSON
    traces. Separating observe from runner keeps scoring pure.

Trade-offs
    Truncates answers to 200 characters. Relies on ``Trace.render_text_report``
    when present; otherwise leaves a blank section. Not a metrics backend.

Edges
    Missing trace → empty named Trace. Missing audits → no audits section.
    Optional ``model`` line appended when provided.
"""

from __future__ import annotations

from typing import Any

from common.tracing import Trace


def render_run_report(result: dict[str, Any], *, model: str = "") -> str:
    """Format one run result as a multi-line text report.

    Purpose
        Produce stdout-friendly diagnostics for CLI ``--report`` and debugging.

    Why
        Lab 16 shape: cost/latency/audit visibility next to the answer.

    Trade-offs
        Best-effort string joining; unknown audit keys print as ``None``.

    Edges
        Always ends with a trailing newline. Empty audits omit the audits
        header entirely.
    """
    trace: Trace = result.get("trace") or Trace(name="empty")
    lines = [
        f"route={result.get('route')} stop_reason={result.get('stop_reason')}",
        f"answer={result.get('answer', '')[:200]}",
        "",
        trace.render_text_report() if hasattr(trace, "render_text_report") else "",
    ]
    audits = result.get("audits") or []
    if audits:
        lines.append("audits:")
        for audit in audits:
            lines.append(
                f"  {audit.get('name')} class={audit.get('classification')} "
                f"executed={audit.get('executed')} decided_by={audit.get('decided_by')}"
            )
    if model:
        lines.append(f"model={model}")
    return "\n".join(lines).rstrip() + "\n"
