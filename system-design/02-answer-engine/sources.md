# Sources - 02 Answer engine

**This case has no T1 sources.** That is the single most important fact about
it, and every reader should register it before using anything here.

## Tier definitions as used in this library

- **T1 first-party**: official documentation, the vendor's own engineering
  writing, papers by the system's authors, or public source code.
- **T2 second-party**: credible outside analysis or reverse engineering. When
  two T2 sources disagree, the disagreement is stated alongside the claim rather
  than resolved silently.
- **T3 inference**: our own reasoning, always phrased as our reading.

## T1

None. Perplexity has not published a first-party architecture description in any
material available to us.

## T2

Both sources are outside reconstructions produced largely by the
search-optimization industry. [T3] Our note on their credibility, which a reader
should weigh: the purpose of this analysis is generally to rank well in the
system rather than to document it accurately. That motivation does not make the
work wrong. It does mean the authors optimize for actionable models of the
system rather than for faithful ones, and that they have no access to the
implementation.

**ziptie.dev reconstruction.** Describes a multi-stage RAG pipeline consisting
of:

- query intent parsing
- real-time hybrid retrieval combining BM25 with dense embeddings
- multi-layer ML ranking with a three-tier reranker
- prompt assembly with citations embedded before generation
- synthesis constrained to the retrieved evidence
- a quality threshold at the third reranking layer, and a fail-safe that
  discards the candidate set and restarts retrieval when too few candidates
  clear it

**stackmatix.com reconstruction.** Describes a three-layer reranking system:

- BM25 plus embedding retrieval
- cross-encoder reranking
- an ML reranker using entity and authority signals
- and states explicitly that its weights are approximate and shift by query type

### Where they agree and disagree

**Agreement, and the only part treated as a lesson in `README.md`:** the shape
is hybrid retrieval, followed by staged reranking, followed by constrained
synthesis. Both describe three ranking stages.

**Disagreement:** what those stages contain. ziptie.dev's three-tier reranker
with a third-layer quality threshold and stackmatix.com's
retrieval, cross-encoder, entity-and-authority sequence are not the same
description. Only ziptie.dev describes the restart fail-safe, so the two sources
also disagree on whether the pipeline contains a loop at all.

**Self-declared uncertainty:** stackmatix.com states its weights are approximate
and shift by query type. This is quoted in `README.md` because a reconstruction
that marks its own limits is more usable than one that does not.

## T3

- **The archetype lesson** in "Why this archetype exists": read-only action space
  plus a hard latency budget inverts the tradeoffs of case 01, and correctness
  is enforced by grounding rather than by verification loops because there is no
  time for a loop. Reasoning from the T2 pipeline shape and from the product
  being interactive.
- **This system sits closer to case 07 than case 01 on the autonomy spectrum**
  (dimension 2). Reasoning from both T2 sources describing fixed stages.
- **Selection is the whole game** (dimension 3). Reasoning from an unbounded
  corpus under a bounded budget.
- **Read-only is why the case 01 permission machinery is absent** (dimension 4).
- **Citations before generation is the transferable idea** (dimension 6 and the
  thing to steal). Reasoning from the ziptie.dev description, contrasted with
  case 03's after-the-fact CitationAgent, which is T1 in its own case.
- **The fail-safe aims at the input rather than the output** (dimensions 8 and
  9). Reasoning from it restarting retrieval rather than regenerating.
- **A hard interactive latency budget, and staged ranking as the response to it**
  (dimension 12). Reasoning from the product shape and from retrieval being
  described as real-time.
- **All four failure modes**, each labelled inline.

## Deliberately excluded

- **Any claim stated as fact about Perplexity.** The warning box exists so that
  this file's contents cannot be quoted as a description of the product, and the
  same caution is repeated in `architecture.md`.
- **Any resolution of the disagreement between the two sources.** We have no
  basis to prefer either account, so both are recorded and neither is adopted.
- **Any model name, index size, latency figure, or ranking weight.** None appears
  in our material. stackmatix.com's own note that its weights are approximate is
  reported as a statement about the reconstruction, not as a weight.
- **Dimensions 7 and 11.** Memory and evaluation are not reconstructable from
  this material, and filling them from general knowledge of search systems would
  produce exactly the kind of confident, sourceless text this library exists to
  avoid.
