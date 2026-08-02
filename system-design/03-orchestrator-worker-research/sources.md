# Sources - 03 Orchestrator-worker research system

Every tier tag in this case folder resolves to an entry here.

## Tier definitions as used in this library

- **T1 first-party**: official documentation, the vendor's own engineering
  writing, papers by the system's authors, or public source code.
- **T2 second-party**: credible outside analysis or reverse engineering.
- **T3 inference**: our own reasoning from a T1 or T2 fact, always phrased as
  our reading.

## T1

**Anthropic, "How we built our multi-agent research system".** This is the sole
source for every factual claim in this case. It backs:

- The definition used throughout: a multi-agent system consists of multiple
  agents, meaning LLMs autonomously using tools in a loop, working together.
- The orchestrator-worker pattern: a lead agent coordinates while delegating
  specialized tasks to subagents operating in parallel.
- The LeadResearcher thinks through the approach and saves its plan to Memory to
  persist context, because if the context window exceeds 200,000 tokens it will
  be truncated and the plan must survive.
- Subagents search independently, each with its own context window, and return
  distilled findings. The lead agent decides whether more research is needed and
  can spawn another wave or refine strategy.
- A separate CitationAgent processes the source documents and the research
  report to identify where citations belong, so claims are attributed.
- A multi-agent system with Claude Opus 4 as lead agent and Claude Sonnet 4
  subagents outperformed single-agent Claude Opus 4 by 90.2% on their internal
  research eval.
- Multi-agent systems use roughly 15 times more tokens than chat interactions.
- Early agents made errors such as spawning 50 subagents for simple queries,
  scouring the web endlessly for nonexistent sources, and distracting each other
  with excessive updates. Prompt engineering was the primary lever for fixing
  these behaviors.
- The approach suits problems that divide into parallel strands and is less
  effective for tightly interdependent tasks such as coding.
- Production concerns named in the post include checkpointing, retry logic, and
  rainbow deployments. Evaluation combined LLM judging with human review, and
  human reviewers caught issues such as overreliance on SEO-optimized sources.

## T2

None. No second-party analysis was used for this case.

## T3

Our inferences, each with the sourced fact it reasons from.

- **Lead and workers have different observation spaces by design**
  (dimension 3). Reasoning from subagents having their own context windows and
  returning distilled findings.
- **The read-only action space is why permissions cost this design almost
  nothing** (dimension 4, dimension 10). Reasoning from the absence of any
  documented external mutation, contrasted against case 01.
- **The CitationAgent exists as a consequence of the context strategy**
  (dimension 5). Reasoning from the lead drafting on distilled findings while
  the CitationAgent is given the source documents. This is the central
  analytical claim of the case and it is ours.
- **Subagents are a context-management primitive before a parallelism
  primitive** (dimension 6). Reasoning from each subagent having its own context
  window, which is a property that would still be needed if the subagents ran
  sequentially.
- **Memory and checkpointing solve two different durability problems**
  (dimension 7). Reasoning from Memory being tied specifically to the truncation
  threshold while checkpointing is named among deployment concerns.
- **Prompting rather than a hard cap was the reported fix for fan-out sizing**
  (dimension 8). Reasoning from the T1 statement that prompt engineering was the
  primary lever, contrasted with the `maxTurns` field in case 01.
- **The production concerns describe a long-running stateful system**
  (dimension 9). Reasoning from rainbow deployments being named, which addresses
  runs that outlive a deploy.
- **The SEO finding is evidence that LLM judges have a blind spot on input
  quality** (dimension 11). Reasoning from that issue being caught by human
  reviewers in a process that also used LLM judging.
- **The lead and worker model split is a cost response to the context strategy**
  (dimension 12). Reasoning from the reported configuration together with the
  token multiple.
- **Attribution drift as a failure mode.** Reasoning from the existence of the
  CitationAgent. Explicitly not a reported incident.

## Deliberately excluded

- **Any characterization of what the 90.2% figure measures.** The post states
  the comparison and names it an internal research eval. What the eval contains,
  how it scores, and what a percentage improvement means on that scale are not
  in our material, so the number is quoted with its stated framing and not
  interpreted.
- **Latency.** The material gives a token multiple and no timing, so dimension
  12 reports tokens only.
- **The subtask specification format and the distillation mechanism.** Both
  would be useful and neither is described. See `open-questions.md`.
- **Any claim that this architecture generalizes to coding.** The post says the
  opposite, and the temptation to soften that into a caveat was declined.
