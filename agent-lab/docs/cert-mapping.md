# Certification mapping

**Exam objectives change, and this table is a hand-written snapshot.** Treat it
as a pointer for where to look, not as a syllabus. Check the official exam
guides directly before planning any study around it:

- Databricks Generative AI Engineer Associate:
  https://www.databricks.com/learn/certification/genai-engineer-associate
- NVIDIA NCA Generative AI LLMs:
  https://www.nvidia.com/en-us/learn/certification/generative-ai-llm-associate/

This table deliberately contains no weightings, no question counts, no passing
scores, and no dates. Those are exactly the details that go stale, and the
official guides are the only place worth reading them.

The Anthropic column refers to the workflow and agent patterns described in
Building Effective Agents and to Effective context engineering for AI agents.
Both are linked in `docs/reading-list.md`.

| Lab | Anthropic pattern or concept | Databricks GenAI Engineer Associate area | NVIDIA NCA-GENL topic |
| --- | --- | --- | --- |
| 00 Setup | The plain model call that the augmented LLM building block augments | Application development including RAG and LLM chains | LLM integration and deployment; Python libraries for LLMs |
| 01 The augmented LLM | The augmented LLM building block; tool use as an agent-computer interface | Application development including RAG and LLM chains; tool and agent frameworks | LLM integration and deployment; prompt engineering |
| 02 Prompt chaining | Prompt chaining: decomposing a task into a fixed sequence with programmatic gates | Problem decomposition and solution design; application development including LLM chains | Prompt engineering; software development |
| 03 Routing | Routing: classifying an input and dispatching to a specialized follow-on call | Problem decomposition and solution design; evaluation and monitoring | Prompt engineering; experimentation; data analysis and visualization |
| 04 Parallelization | Parallelization in both variants: sectioning and voting | Problem decomposition and solution design; evaluation and monitoring | Software development; experimentation |
| 05 Orchestrator and workers | Orchestrator-workers: a lead call that decomposes dynamically and synthesizes worker output | Problem decomposition and solution design; tool and agent frameworks | Prompt engineering; software development |
| 06 Evaluator and optimizer | Evaluator-optimizer: a generator and critic loop with explicit stopping criteria | Evaluation and monitoring including custom scorers; application development | Prompt engineering; alignment; experimentation |
| 07 Tool design and the agent-computer interface | Agent-computer interface design: tool schemas, naming, descriptions, and error design | Tool and agent frameworks; evaluation and monitoring | Prompt engineering; software development; experimentation |
| 08 RAG basics | The retrieval half of the augmented LLM building block; grounding and citation | Data preparation and chunking; application development including RAG | Data preprocessing and feature engineering; Python libraries for LLMs |
| 09 Retrieval quality | Retrieval quality as part of context engineering: getting the right tokens into the window | Data preparation and chunking; evaluation and monitoring including custom scorers | Data analysis and visualization; experimentation; data preprocessing and feature engineering |
| 10 An MCP-style server | Agent-computer interface design across a protocol boundary; tool discovery at runtime | Tool and agent frameworks including MCP servers | Software development; LLM integration and deployment |
| 11 Context and memory | Effective context engineering: token budgeting, compaction, and keeping detail outside the window | Application development including LLM chains; governance | Prompt engineering; software development; data preprocessing and feature engineering |
| 12 The agent loop | The autonomous agent loop and its stopping conditions; when to use an agent instead of a workflow | Tool and agent frameworks; evaluation and monitoring | Software development; LLM integration and deployment |
| 13 Subagents | Orchestrator-workers taken to the agent level; capability restriction as design | Tool and agent frameworks; problem decomposition and solution design | Software development; experimentation |
| 14 Human in the loop | Human oversight at the agent-computer interface; designing for recoverable errors | Governance; tool and agent frameworks | Alignment; software development |
| 15 Evaluation | Evaluator-optimizer applied as an offline regression suite; measuring before optimising | Evaluation and monitoring including custom scorers; governance | Experimentation; data analysis and visualization; alignment |
| 16 Observability | Observability for agent runs; measuring context and cost per step | Evaluation and monitoring including MLflow tracing; assembling and deploying applications | Data analysis and visualization; software development; experimentation |
| 17 Guardrails | Guardrails at the agent-computer interface; treating tool results as untrusted data | Governance; application development including RAG and LLM chains | Alignment; prompt engineering; software development |
| 18 Packaging and deployment | Taking an agent to production: one core behind thin entry points | Assembling and deploying applications; governance | LLM integration and deployment; software development |

## How to use this

The labs are not organised around either exam, and neither exam is organised
around the labs. The overlap is real but partial: this course goes deeper on
agent loops, tool interface design, and context engineering than either exam
requires, and it does not cover model training, embeddings at scale, or any
vendor-specific platform tooling that the exams do cover.

If you are preparing for the Databricks exam, note that its platform-specific
material, including MLflow and Unity Catalog, is not taught here. Labs 15 and 16
cover the concepts that MLflow tracing and custom scorers implement, which makes
the platform material easier to learn, but they are not a substitute for it.

If you are preparing for the NVIDIA exam, note that its machine learning and
neural network fundamentals are assumed rather than taught here. This course
starts at the API boundary and works outward toward systems.
