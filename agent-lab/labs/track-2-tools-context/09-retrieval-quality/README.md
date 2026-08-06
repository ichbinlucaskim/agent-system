# Lab 09 - Retrieval quality

## Goal

After this lab you can measure retrieval instead of guessing at it: compute recall at k against a labelled set, sweep chunk sizes, combine keyword and vector scores into a hybrid ranking, and add a reranking pass.

## Prerequisites

Lab 08. Concepts: recall at k, and the idea that a retrieval change without a metric is a coin flip.

## Estimated time

60 to 90 minutes

## Background

This lab is marked optional because the pipeline in lab 08 already works. It is the lab that decides whether your pipeline works well, and in a real system it is usually where most of the quality actually comes from.

Recall at k asks a narrow, answerable question: of the passages that should have been retrieved, how many appeared in the top k. It needs a labelled set, which for a small corpus means writing down twenty queries and the chunk that answers each one. That afternoon of labelling is what converts every later change from an opinion into a measurement.

A labelled set also fixes the resolution of every number you are about to read. With twenty eight queries, one query is worth 0.036, so a gap of 0.02 between two strategies is not a small win, it is nothing. Print `1/len(queries)` next to your tables and you will stop chasing differences your set cannot see.

Two things have to be true before a measurement means anything, and both are easy to get wrong here. The first is that the score depends only on what you meant to vary. Ranking leaves ties all over the place on a small corpus, and if ties fall back to the order documents were declared in, then reordering the corpus changes the score: a real improvement and a lucky ordering become indistinguishable. Break every tie on something intrinsic, like the chunk id. The second is that zero overlap is not a weak keyword hit, it is not a hit. An inverted index returns nothing for a query with no matching token; a ranking that instead returns the whole corpus in dict order will score whatever happens to be listed first, which can flatter keyword search into looking like the best strategy you have.

Chunk size has no universal right answer, which is why you sweep it. Hold the queries and the labels fixed, rebuild the store at several sizes, and plot recall against size. Pick sizes that actually chunk the corpus differently: documents shorter than the size fit in one chunk, so two large sizes can produce byte-identical stores and a flat line that looks like a plateau while measuring nothing. Read the spread in units of queries. If the whole sweep fits inside one or two queries, the honest conclusion is that chunk size is not your lever here, and the next hour is better spent on reranking.

Keyword and vector search fail in different directions. Vector search finds passages that mean the same thing in different words; keyword search finds exact identifiers, error codes, and product names that an embedding smears into its neighbours. Hybrid scoring takes a weighted sum of the two, and the weight is a knob you tune on the labelled set rather than a constant you copy from somewhere. Sweep alpha and look for an interior optimum: a middle alpha that beats both alpha 0 and alpha 1 is the evidence that the two signals really do fail on different queries. If the best alpha sits at an endpoint, the combination is buying you nothing and you should drop it.

The moment you tune a knob, the set you tuned on stops being able to tell you how good the result is. Choosing the best of five alphas and then quoting that alpha's score on the same queries reports the best of five tries. So split the labelled set: choose on one half, quote the other. Splitting costs resolution, since two halves of fourteen resolve 1/14 each rather than 1/28, which is one more reason the set wants to be large. Report both halves side by side and two separate things become visible. The gap on the strategy you tuned is the price of tuning. The gap on strategies you never touched is split noise, and when that one is the larger of the two, neither half's number means much on its own yet.

Reranking is a second, more expensive pass over a shortlist. Retrieve twenty cheaply, then score those twenty carefully and keep the best three. It works because ranking twenty candidates precisely is affordable while ranking the whole corpus precisely is not, and it usually buys more than another round of chunk-size tuning. Two details decide whether it buys anything at all. The careful scorer has to differ from the cheap one, or reranking simply reapplies the blindness it exists to repair. And the shortlist has to be generous, because a document the cheap pass never retrieved can never be promoted by the careful one.

## Steps

1. Write `CORPUS` and `LABELLED_QUERIES`: a few documents long enough that the chunk size changes how they split, and at least fifteen `(query, relevant_document_ids)` pairs over them. Label documents rather than chunk ids, because chunk ids change at every size in the sweep. Everything else in this lab depends on this list being honest.
2. Implement `recall_at_k`, and `keyword_ranked` alongside it: rank by keyword overlap, leave out the chunks that match nothing, and break remaining ties on chunk id so no ranking can depend on corpus order.
3. Implement `sweep_chunk_sizes` and pick `SWEEP_SIZES` so that each size chunks the corpus differently, otherwise the sweep repeats one experiment and reports it as a plateau.
4. Implement `hybrid_score`, `tune_alpha`, and `split_queries`: combine a normalised keyword score and a normalised vector score with a weight alpha, check that alpha of 0 and 1 reproduce the pure strategies, then measure a range of alphas on one half of the labelled set and keep the other half back for reporting.
5. Implement `careful_score` and `rerank`: score a shortlist with a pass that is deliberately different from plain keyword overlap, and return the same hits in a new order.
6. Implement `evaluate`: report recall at k for the vector, keyword, hybrid, and reranked strategies on the same labelled set, in one table, giving the reranker a generous shortlist.

## Verification

```bash
pytest labs/track-2-tools-context/09-retrieval-quality/tests -v
```

Every metric in this lab is arithmetic and runs offline. Passing means recall at k matches hand-counted examples including the edge cases, the sweep returns one entry per chunk size and no two of those sizes chunk the corpus identically, hybrid scoring reduces to the pure strategies at the extremes of alpha, and reranking returns a permutation of its input rather than silently dropping candidates.

The split is checked too: the two halves have to be disjoint, or a knob chosen on one is being graded on itself, and both halves have to cover every document, or a half cannot score what it never asks about.

Three of the tests are there because the obvious implementation passes everything else while still being wrong. **Reordering the corpus must not move any score**, which fails the moment a ranking lets ties fall back to dict order. **Reranking must promote the best candidate**, not just return a subset, because a `rerank` that returns `hits[:keep]` untouched satisfies every permutation check. And **the careful scorer must find a match that plain overlap misses**, or the expensive pass is the cheap pass with extra steps.

## Going further

- Add queries that use a synonym never present in the corpus, and see how much of the gap hybrid scoring closes.
- Measure recall at 1, 3, and 10 for the same strategies. A strategy that wins at 10 and loses at 1 is a reranking opportunity.
- Time the reranking pass and decide whether the recall it buys is worth the latency for an interactive application.
- Shrink the shortlist passed to `rerank` down to 3 and watch the reranked score fall back towards the cheap ranking. That is the floor on how much a careful pass can repair.
- Put the zero-overlap chunks back into `keyword_ranked` and reorder the corpus. Watching one strategy's score swing while the others hold still is the clearest picture of why ties need an intrinsic tiebreaker.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Retrieval quality as part of context engineering: getting the right tokens into the window.
- **Databricks Generative AI Engineer Associate**: Data preparation and chunking; evaluation and monitoring including custom scorers.
- **NVIDIA NCA Generative AI LLMs**: Data analysis and visualization; experimentation; data preprocessing and feature engineering.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
