# Reading list

This list is deliberately short. Every entry below is a source this course is
built on, and nothing is included that could not be named exactly.

## Primary sources

- Anthropic, "Building Effective Agents"
  https://www.anthropic.com/engineering/building-effective-agents

  The source of the workflow and agent patterns used throughout track 1: the
  augmented LLM building block, prompt chaining, routing, parallelization,
  orchestrator-workers, and evaluator-optimizer. It also covers the
  agent-computer interface idea that lab 07 is built around, and the question of
  when an agent is the wrong choice.

- Anthropic, "Effective context engineering for AI agents"
  https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

  The source for track 2's treatment of the context window as a budget rather
  than a container. Read it before lab 11.

## Certification guides

- Databricks Generative AI Engineer Associate
  https://www.databricks.com/learn/certification/genai-engineer-associate

- NVIDIA NCA Generative AI LLMs
  https://www.nvidia.com/en-us/learn/certification/generative-ai-llm-associate/

Read the exam objectives from these pages directly. `docs/cert-mapping.md` maps
the labs onto them, but that mapping is a hand-written snapshot and the official
pages are authoritative.

## API and SDK documentation

Anthropic API and Claude Agent SDK documentation lives under `docs.claude.com`.
Navigate from there rather than following a deep link from memory or from a blog
post. Deep links into API documentation go stale faster than almost anything
else, and a link that silently redirects to a different version of a page is
worse than no link at all.

The pages worth finding on your own, in roughly the order this course needs
them: the Messages API reference, streaming, tool use, prompt caching, extended
and adaptive thinking, and token counting.

## A note on what is not here

There are no papers, arXiv numbers, or third-party blog posts in this list. That
is not a judgment about their quality. It is because a reading list is only
useful if every entry can be trusted to exist under the exact title given, and
this list is limited to entries that meet that bar. Add your own as you find
them, and record the exact title and URL when you do.
