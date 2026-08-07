# Workflow versus agent

A workflow is a predetermined sequence of LLM calls and code gates. The
developer chooses what happens next. An agent is a loop where the model
chooses the next tool or step.

Use a workflow when the path is known and latency is tight. Use an agent when
the next action cannot be planned in advance. Mixing them is common: a
workflow may open a bounded agent loop on one branch only.
