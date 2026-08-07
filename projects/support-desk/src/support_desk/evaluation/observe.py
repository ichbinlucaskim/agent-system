"""Turn a Trace into a short cost and latency report (lab 16)."""

from __future__ import annotations

from typing import Any

from common.tracing import Trace


def render_run_report(result: dict[str, Any], *, model: str = "") -> str:
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
