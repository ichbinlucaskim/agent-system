"""Lab 13 - Subagents (reference solution).

A subagent is a child agent with a fresh context window, its own system
prompt, and a tool set narrower than its parent's. The parent hands it a
task and reads back a report; everything the child read along the way
stays out of the parent's context. The lab ends in a measurement of what
that isolation costs and buys.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable

from common.client import complete, complete_with_tools, text_of, tool_uses
from common.cost import TokenUsage, usage_of

# One shared budget shape for both approaches keeps the comparison honest.
DEFAULT_MAX_STEPS = 6

SINGLE_AGENT_SYSTEM = (
    "You are a research assistant. Use the tools to read the project notes, "
    "then answer the question. Answer from the notes only."
)

PARENT_SYSTEM = (
    "You are the lead researcher. You receive reports from assistants who "
    "have already read the notes. Combine their reports into one answer. "
    "Do not speculate beyond what the reports say."
)

# A small corpus the demo tools read from. Live state stands in for the
# forty files a real subagent would grind through.
NOTES: dict[str, str] = {
    "returns.md": (
        "Returns are accepted within 30 days of delivery. Opened software "
        "is not returnable."
    ),
    "shipping.md": (
        "Standard shipping takes 3 to 5 business days. Express orders "
        "placed before 2pm arrive the next business day."
    ),
    "warranty.md": (
        "Hardware carries a 12 month warranty for manufacturing defects. "
        "Accidental damage is excluded."
    ),
}

ALL_TOOLS: list[dict[str, Any]] = [
    {
        "name": "list_notes",
        "description": "List the filenames of every project note.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_note",
        "description": "Read the full text of one project note by filename.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "A filename returned by list_notes.",
                }
            },
            "required": ["filename"],
        },
    },
]


def execute_tool(name: str, arguments: dict[str, Any]) -> tuple[str, bool]:
    """Run one demo tool. Returns (result_text, is_error)."""
    if name == "list_notes":
        return (", ".join(sorted(NOTES)), False)
    if name == "read_note":
        filename = str(arguments.get("filename", "")).strip()
        if filename not in NOTES:
            known = ", ".join(sorted(NOTES))
            return (f"Error: no note {filename!r}. Notes: {known}.", True)
        return (NOTES[filename], False)
    return (f"Error: unknown tool {name!r}.", True)


@dataclass(frozen=True)
class SubagentSpec:
    """The definition of one child agent: prompt, tools, and budget."""

    name: str
    system: str
    # Tool names only, not definitions: restrict_tools must resolve them
    # against the parent's real set, so a typo fails loudly instead of
    # quietly granting nothing.
    allowed_tools: list[str]
    max_steps: int = DEFAULT_MAX_STEPS


def restrict_tools(
    all_tools: list[dict[str, Any]], allowed: list[str]
) -> list[dict[str, Any]]:
    """Return only the tool definitions a spec is allowed to use."""
    known = {tool["name"] for tool in all_tools}
    missing = [name for name in allowed if name not in known]
    if missing:
        # Silently returning fewer tools would look like the model choosing
        # not to use one; a typo must fail where it was written.
        raise ValueError(
            f"spec allows tools the parent does not have: {missing}. "
            f"Parent tools: {sorted(known)}."
        )
    return [tool for tool in all_tools if tool["name"] in allowed]


def _live_model_call(
    messages: list[dict[str, Any]], tools: list[dict[str, Any]], system: str
) -> Any:
    if tools:
        return complete_with_tools(messages, tools, system=system)
    return complete(messages, system=system)


def _agent_run(
    task: str,
    system: str,
    tools: list[dict[str, Any]],
    max_steps: int,
    model_call: Callable[..., Any] | None,
    executor: Callable[[str, dict[str, Any]], tuple[str, bool]] | None,
) -> dict[str, Any]:
    """The shared loop: one agent, one fresh message list, a step budget."""
    call = model_call or _live_model_call
    run_tool = executor or execute_tool
    allowed = {tool["name"] for tool in tools}
    messages: list[dict[str, Any]] = [{"role": "user", "content": task}]
    usage = TokenUsage()
    steps = 0
    report = ""

    for _ in range(max_steps):
        response = call(messages, tools, system)
        steps += 1
        usage = usage + usage_of(response)
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            report = text_of(response)
            break
        results: list[dict[str, Any]] = []
        for block in tool_uses(response):
            if block.name not in allowed:
                # Capability is granted by construction: the definition was
                # never sent, and a request naming it anyway is refused here
                # rather than executed.
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": (
                            f"Error: tool {block.name!r} is not available "
                            f"to this agent."
                        ),
                        "is_error": True,
                    }
                )
                continue
            output, is_error = run_tool(block.name, dict(block.input))
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                    "is_error": is_error,
                }
            )
        messages.append({"role": "user", "content": results})

    return {"report": report, "usage": usage, "steps": steps, "messages": messages}


def run_subagent(
    spec: Any,
    task: str,
    all_tools: list[dict[str, Any]],
    *,
    model_call: Callable[..., Any] | None = None,
    executor: Callable[[str, dict[str, Any]], tuple[str, bool]] | None = None,
) -> dict[str, Any]:
    """Run one child agent with its own context and restricted tools."""
    tools = restrict_tools(all_tools, spec.allowed_tools)
    # The message list starts empty apart from the task itself. Passing any
    # parent history here would defeat the entire point of the pattern.
    result = _agent_run(task, spec.system, tools, spec.max_steps, model_call, executor)
    result["name"] = spec.name
    return result


def single_agent(
    task: str,
    all_tools: list[dict[str, Any]],
    *,
    model_call: Callable[..., Any] | None = None,
    executor: Callable[[str, dict[str, Any]], tuple[str, bool]] | None = None,
) -> dict[str, Any]:
    """Baseline: one agent, all tools, no delegation."""
    # The control in the experiment: same task, same model, same budget
    # shape, so any difference in the totals comes from delegation alone.
    started = time.perf_counter()
    result = _agent_run(
        task, SINGLE_AGENT_SYSTEM, all_tools, DEFAULT_MAX_STEPS, model_call, executor
    )
    result["answer"] = result.pop("report")
    result["seconds"] = time.perf_counter() - started
    return result


def with_subagents(
    task: str,
    specs: list[Any],
    all_tools: list[dict[str, Any]],
    *,
    model_call: Callable[..., Any] | None = None,
    executor: Callable[[str, dict[str, Any]], tuple[str, bool]] | None = None,
) -> dict[str, Any]:
    """Fan out to subagents and let the parent read only the reports."""
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max(len(specs), 1)) as pool:
        futures = [
            pool.submit(
                run_subagent,
                spec,
                task,
                all_tools,
                model_call=model_call,
                executor=executor,
            )
            for spec in specs
        ]
        reports = [future.result() for future in futures]

    # The parent sees one paragraph per child, never the transcripts. This
    # line is where the context isolation actually happens.
    briefing = "\n\n".join(f"[{r['name']}] {r['report']}" for r in reports)
    call = model_call or _live_model_call
    messages = [
        {
            "role": "user",
            "content": (
                f"Task: {task}\n\nReports from your assistants:\n{briefing}\n\n"
                f"Write the final answer."
            ),
        }
    ]
    response = call(messages, [], PARENT_SYSTEM)

    usage = usage_of(response)
    for report in reports:
        usage = usage + report["usage"]
    return {
        "answer": text_of(response),
        "usage": usage,
        "steps": sum(r["steps"] for r in reports) + 1,
        "reports": reports,
        "seconds": time.perf_counter() - started,
    }


def compare(
    task: str,
    specs: list[Any],
    all_tools: list[dict[str, Any]],
    *,
    model_call: Callable[..., Any] | None = None,
    executor: Callable[[str, dict[str, Any]], tuple[str, bool]] | None = None,
) -> dict[str, Any]:
    """Run both approaches and report tokens, time, and answers."""
    single = single_agent(task, all_tools, model_call=model_call, executor=executor)
    delegated = with_subagents(
        task, specs, all_tools, model_call=model_call, executor=executor
    )
    # A measurement, not an opinion: both runs side by side, and the reader
    # decides whether the isolation paid for the overhead on this task.
    return {
        "single": {
            "answer": single["answer"],
            "total_tokens": single["usage"].total_tokens,
            "steps": single["steps"],
            "seconds": single["seconds"],
        },
        "subagents": {
            "answer": delegated["answer"],
            "total_tokens": delegated["usage"].total_tokens,
            "steps": delegated["steps"],
            "seconds": delegated["seconds"],
        },
    }


def main() -> int:
    """Run the same task both ways and print the totals side by side."""
    task = (
        "What is the return window, and how fast can an express order "
        "arrive? Cite the note filenames."
    )
    specs = [
        SubagentSpec(
            name="returns-reader",
            system=(
                "You answer questions about returns only. Read the notes "
                "you need and reply with a two sentence report."
            ),
            allowed_tools=["list_notes", "read_note"],
        ),
        SubagentSpec(
            name="shipping-reader",
            system=(
                "You answer questions about shipping only. Read the notes "
                "you need and reply with a two sentence report."
            ),
            allowed_tools=["list_notes", "read_note"],
        ),
    ]

    result = compare(task, specs, ALL_TOOLS)
    for label in ("single", "subagents"):
        run = result[label]
        print(
            f"{label:<10} steps={run['steps']} tokens={run['total_tokens']} "
            f"seconds={run['seconds']:.1f}"
        )
        print(f"{'':<10} {run['answer']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
