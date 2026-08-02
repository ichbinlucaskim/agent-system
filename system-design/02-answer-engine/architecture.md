# Architecture - 02 Answer engine

> **Every box below is second-party reconstruction.** No first-party
> architecture description exists in our material. Where the two sources
> disagree, the diagram shows both rather than picking one.

## Shape

```text
                        query
                          |
                          v
              +------------------------+
              |  query intent parsing  |   [T2] ziptie.dev
              +------------------------+   (stackmatix.com does not
                          |                 describe this stage)
                          v
              +------------------------+
              |  hybrid retrieval      |   [T2] BOTH sources agree:
              |  BM25 + dense          |        BM25 combined with
              |  embeddings            |        embedding retrieval
              +------------------------+   [T2] ziptie.dev: "real-time"
                          |
                          v
        ==================================================
         staged reranking
         [T2] BOTH sources agree there are three stages
         [T2] the sources DISAGREE on their contents:
        ==================================================
              ziptie.dev            |   stackmatix.com
              --------------------- | ---------------------
              multi-layer ML        |   layer 1: BM25 +
              ranking with a        |     embedding retrieval
              three-tier reranker   |   layer 2: cross-encoder
                                    |     reranking
              quality threshold     |   layer 3: ML reranker
              at the third layer    |     using entity and
                                    |     authority signals
                                    |
                                    |   [T2] weights stated to be
                                    |   approximate and to shift
                                    |   by query type
        ==================================================
                          |
              +-----------+------------+
              |                        |
       enough candidates        too few clear the
       clear the bar            threshold
              |                        |
              |                        v
              |          +--------------------------------+
              |          |  discard candidate set and     |  [T2] ziptie.dev
              |          |  restart retrieval             |  only; not in
              |          +--------------------------------+  stackmatix.com
              |                        |
              |                        +-----> back to hybrid retrieval
              v
              +------------------------+
              |  prompt assembly with  |   [T2] ziptie.dev: citations
              |  citations embedded    |        embedded BEFORE
              |  before generation     |        generation
              +------------------------+
                          |
                          v
              +------------------------+
              |  synthesis constrained |   [T2] ziptie.dev
              |  to retrieved evidence |
              +------------------------+
                          |
                          v
                    cited answer
```

## Flow

1. [T2] A query is parsed for intent (ziptie.dev).
2. [T2] Hybrid retrieval combines BM25 with dense embeddings. Both sources
   describe this stage, and it is the strongest point of agreement between them.
3. [T2] Candidates pass through three ranking stages. Both sources describe
   three; they describe different threes.
4. [T2] A quality threshold applies at the third layer, and a fail-safe discards
   the candidate set and restarts retrieval when too few candidates clear it
   (ziptie.dev only).
5. [T2] Citations are embedded during prompt assembly, before generation
   (ziptie.dev).
6. [T2] Synthesis is constrained to the retrieved evidence (ziptie.dev).

## Boundaries

**Retrieval to ranking.** [T3] Our reading: this is where the latency budget is
spent, and staged ranking is the mechanism for spending it unevenly. Cheap
methods run over many candidates, expensive ones over few.

**Ranking to generation.** [T2] ziptie.dev places citation assembly at this
boundary, before the model generates. [T3] Our reading: this is the single most
consequential boundary in the design, because it determines whether attribution
is a constraint on generation or a reconstruction afterwards. Case 03 is on the
other side of the same choice.

**The absent boundary.** [T3] There is no verification stage after generation in
either reconstruction. Whether the answer is supported by the evidence is never
checked once the answer exists, which is what a hard latency budget buys you.

## What this diagram does not show

- **Anything first-party.** This bears repeating at the bottom of the file as
  well as the top.
- **Ground truth on the reranking stack.** Two mutually inconsistent accounts are
  both drawn. At most one is right, and possibly neither.
- **Conversational state, personalization, or caching.** Not described in either
  source. Unknown.
- **Evaluation.** Not described in either source. Unknown.
- **Any figure.** No latency, cost, corpus size, or candidate count appears in
  our material, and none is estimated.
