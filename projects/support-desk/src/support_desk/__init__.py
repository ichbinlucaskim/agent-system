"""Support desk: layered worked example of system-design case 06.

Package layout matches the five layers:

1. ``tools_gate``   — tools, HITL, DB, policy retrieval, guardrails
2. ``routing``      — FAQ vs account
3. ``agent``        — loop, budgets, stop reasons
4. ``evaluation``   — action-level suite and reports
5. ``packaging``    — config, CLI/HTTP, smoke, MCP adapter
"""

__version__ = "0.1.0"
