# 02 - Answer engine

## Representative system

Perplexity, as reconstructed by outside parties.

> ## Warning: this is a reconstruction, not a description
>
> **Perplexity has not published a first-party architecture description.**
> Nothing in this file is T1. Everything below comes from outside
> reconstruction, largely produced by the search-optimization industry, whose
> purpose in analyzing this system is to rank in it rather than to document it.
>
> **The two reconstructions used here disagree on specifics.** They agree on the
> overall shape and diverge on what the stages contain, which is exactly the
> pattern you would expect from independent inference about a system neither
> author can see.
>
> **This document is a study of the archetype, not a claim about the product.**
> Read it for what an answer engine has to be, given a read-only action space
> and a hard latency budget. Do not cite it for what Perplexity does. Several
> dimensions below are marked as not reconstructable and are left empty rather
> than filled from the same industry commentary that produced the rest.

## Why this archetype exists

This case inverts almost every tradeoff in case 01.

[T3] Our reading: this is an agent-adjacent system with a read-only action space
and a hard latency budget. Case 01 can take as long as it needs and its actions
bite, so its design budget goes to permissions and its correctness comes from a
human reviewing the result. Here nothing the system does is dangerous and
nothing it does can be slow, so the entire design problem moves to getting the
right evidence in front of the model on the first attempt.

The consequence, and the reason this case earns a place, is that **correctness
is enforced by grounding rather than by verification loops, because there is no
time for a loop.** Case 03 verifies attribution with a separate agent after
drafting. Case 04 runs tests and tries again. Case 06 can afford a validity
check before acting. This case can do none of that, and has to solve
correctness structurally instead.

## The twelve dimensions

Dimensions are filled only where the two reconstructions support them. Several
are empty on purpose.

### 1. Problem and success criteria

[T3] Answer a natural-language question with a synthesized response whose claims
are attributable to retrieved sources, within an interactive latency budget.

[T3] Success has the same two-part structure as case 06, and the parts are
different: the answer must be useful, and it must be supported by what was
retrieved. A fluent answer that outruns its evidence is the characteristic
failure of the archetype.

### 2. Autonomy level

[T2] Both reconstructions describe a staged pipeline rather than a model
directing its own process: ziptie.dev describes query intent parsing, retrieval,
ranking, prompt assembly, and synthesis as sequential stages; stackmatix.com
describes retrieval followed by two further reranking layers.

[T3] Our reading, and it is worth stating plainly: if these reconstructions are
even approximately right, this system belongs closer to case 07 than to case 01
on the autonomy spectrum. It is in this library as an agent-adjacent case
because of what it does, not because of how it is controlled.

### 3. Observation space

[T2] A web-scale corpus reached through retrieval. ziptie.dev describes
real-time hybrid retrieval combining BM25 with dense embeddings; stackmatix.com
describes BM25 plus embedding retrieval as the first layer of three.

[T3] Our reading: the observation space is effectively unbounded and the
system's real constraint is not what it can see but how much of it can be looked
at within the budget, which makes selection the whole game.

### 4. Action space

[T3] Read-only. Retrieval, ranking, and generation produce a response and change
nothing outside the system.

[T3] This single property is why the permission machinery that dominates case 01
is absent here, and it is the cleanest illustration in the library of dimension
4 driving a design. Two systems can both be built around an LLM and share almost
no safety architecture because one can only read.

### 5. Tools and agent-computer interface

[T2] The components described are retrieval and reranking stages rather than
tools a model selects among. ziptie.dev describes multi-layer ML ranking with a
three-tier reranker; stackmatix.com describes a three-layer reranking system of
BM25 plus embedding retrieval, then cross-encoder reranking, then an ML reranker
using entity and authority signals.

[T2] The two accounts differ on what the layers contain. stackmatix.com states
that its weights are approximate and shift by query type, which is an unusually
explicit admission of the limits of a reconstruction and is worth taking at face
value.

[T3] Our reading: there is no agent-computer interface here in the sense case 04
means, because the model is not choosing actions. The interface design work is
in the ranking stack.

### 6. Context strategy

[T2] ziptie.dev describes prompt assembly with citations embedded before
generation, and synthesis constrained to the retrieved evidence.

[T3] Our reading, and the most transferable observation in this case: attaching
citations before generation rather than after is a structural choice with a
direct consequence. Case 03 attributes after drafting with a separate agent,
which is the only option available once the drafting agent no longer holds the
sources. Here the sources are still present at generation time, so attribution
can be a property of the prompt instead of a later reconstruction. The latency
budget forces this, and the result is arguably stronger than the alternative.

### 7. Memory and state

Not reconstructable from our material. Neither source describes conversational
state, personalization, or caching across queries. Left empty rather than filled
by analogy. See `open-questions.md`.

### 8. Control flow

[T2] Predominantly fixed. ziptie.dev describes one departure from a straight
pipeline: a quality threshold at the third reranking layer, with a fail-safe
that discards the candidate set and restarts retrieval when too few candidates
clear it.

[T2] stackmatix.com does not describe this fail-safe. The two sources are
therefore in tension on whether the pipeline has a loop in it at all, and we
have no way to resolve that.

[T3] Our reading: if the fail-safe exists as described, it is the design's one
concession to iteration, and its shape is telling. It restarts retrieval rather
than regenerating the answer, which is what a system with no time for a
verification loop does instead of verifying.

### 9. Error handling and recovery

[T2] The fail-safe above is the only recovery mechanism described in either
source: when too few candidates clear the quality threshold, the candidate set
is discarded and retrieval restarts.

[T3] Our reading: this is recovery aimed at the input rather than the output. It
treats a weak evidence set as the failure to be caught, which follows from
dimension 1, where a fluent answer outrunning its evidence is the failure that
matters.

### 10. Human involvement and permissions

[T3] None during a query, which follows from the read-only action space. There
is nothing to approve.

### 11. Evaluation

Not reconstructable from our material. Neither source describes how the system
is evaluated, which is unsurprising, since evaluation is internal and outside
reconstruction works from observed outputs. Left empty. See
`open-questions.md`.

### 12. Cost and latency budget

[T3] A hard interactive budget, inferred from the product being a
question-answering interface and from [T2] retrieval being described as
real-time.

[T3] Our reading: this is the constraint the whole architecture is organized
around, and it is the reason the staged rerankers exist. Ranking in tiers is how
you spend increasing amounts of compute on a shrinking candidate set, which is
the standard answer to a budget that forbids evaluating everything carefully.
Neither source gives a figure and neither do we.

## Failure modes

- **A fluent answer that outruns its evidence.** [T3] The archetype's defining
  failure, and the one that grounding is meant to structurally prevent. Reasoned
  from the design rather than observed.
- **A weak candidate set that clears no quality bar.** [T2] ziptie.dev describes
  a fail-safe for precisely this, which is evidence that the failure is real
  enough to have been engineered against, at least in that author's
  reconstruction.
- **Ranking that is confidently wrong on an unusual query type.**
  [T2] stackmatix.com notes that weights shift by query type. [T3] Our reading
  is that a ranking stack tuned across query types will have types it serves
  worse, and that nothing in a read-only pipeline surfaces this to the user,
  because the answer looks the same either way.
- **No mechanism to notice the question was misread.** [T2] Query intent parsing
  is described as the first stage. [T3] Our reading: an error there propagates
  through every later stage, and a pipeline without a verification loop has no
  place to catch it.

## One thing to steal

Embed the citations before generation rather than attaching them after.

[T2] ziptie.dev describes prompt assembly with citations embedded before
generation and synthesis constrained to the retrieved evidence. [T3] Our reading
of why this generalizes: attribution added after the fact is a reconstruction
problem, and case 03 has to build a whole separate agent to solve it.
Attribution present at generation time is a constraint on the generation
instead. Any system that still holds its sources when it drafts should prefer
the second, and most systems give up that position by summarizing earlier than
they need to.

## One thing not to copy

The reranker internals, in any specific form.

The two reconstructions agree that there is a staged ranking stack and disagree
about what is in it. [T2] stackmatix.com describes cross-encoder reranking
followed by an ML reranker using entity and authority signals, and says its
weights are approximate and shift by query type. [T2] ziptie.dev describes a
three-tier reranker with a quality threshold at the third layer. [T3] Our
reading: copying either specification means copying an outside guess about a
system neither author can see. The shape, which is hybrid retrieval followed by
staged reranking followed by constrained synthesis, is what both agree on and is
the only part that should be treated as a lesson.

## Related

**Lab exercises:** `08-rag-basics`, `09-retrieval-quality`, `03-routing`,
`02-prompt-chaining`.

**Paper topics:** `04-memory-and-retrieval`, `07-evaluation`.

**Other cases:** `01-terminal-coding-agent` is the inversion this case is
paired with. `03-orchestrator-worker-research` solves the attribution problem
from the opposite end. `07-workflow-not-agent` is where this case arguably
belongs on the autonomy spectrum.
