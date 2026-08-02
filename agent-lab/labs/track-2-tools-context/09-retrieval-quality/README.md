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

Chunk size has no universal right answer, which is why you sweep it. Hold the queries and the labels fixed, rebuild the store at several sizes, and plot recall against size. The curve usually has a broad plateau, and knowing where the plateau starts matters more than finding a single optimum.

Keyword and vector search fail in different directions. Vector search finds passages that mean the same thing in different words; keyword search finds exact identifiers, error codes, and product names that an embedding smears into its neighbours. Hybrid scoring takes a weighted sum of the two, and the weight is a knob you tune on the labelled set rather than a constant you copy from somewhere.

Reranking is a second, more expensive pass over a shortlist. Retrieve twenty cheaply, then score those twenty carefully and keep the best three. It works because ranking twenty candidates precisely is affordable while ranking the whole corpus precisely is not, and it usually buys more than another round of chunk-size tuning.

## Steps

1. Write `LABELLED_QUERIES`: at least fifteen `(query, relevant_chunk_ids)` pairs over the lab 08 corpus. Everything else in this lab depends on this list being honest.
2. Implement `recall_at_k`: given retrieved ids and relevant ids, return the fraction of relevant ids that appear in the top k.
3. Implement `sweep_chunk_sizes`: rebuild the store at several chunk sizes and return recall at k for each, so the trade-off is visible as a table.
4. Implement `hybrid_score`: combine a normalised keyword score and a normalised vector score with a weight alpha, and check that alpha of 0 and 1 reproduce the pure strategies.
5. Implement `rerank`: take a shortlist and reorder it with a more careful scoring pass, returning the same set of hits in a new order.
6. Implement `evaluate`: report recall at k for the vector, keyword, hybrid, and reranked strategies on the same labelled set, in one table.

## Verification

```bash
pytest labs/track-2-tools-context/09-retrieval-quality/tests -v
```

Every metric in this lab is arithmetic and runs offline. Passing means recall at k matches hand-counted examples including the edge cases, the sweep returns one entry per chunk size, hybrid scoring reduces to the pure strategies at the extremes of alpha, and reranking returns a permutation of its input rather than silently dropping candidates.

## Going further

- Add queries that use a synonym never present in the corpus, and see how much of the gap hybrid scoring closes.
- Measure recall at 1, 3, and 10 for the same strategies. A strategy that wins at 10 and loses at 1 is a reranking opportunity.
- Time the reranking pass and decide whether the recall it buys is worth the latency for an interactive application.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Retrieval quality as part of context engineering: getting the right tokens into the window.
- **Databricks Generative AI Engineer Associate**: Data preparation and chunking; evaluation and monitoring including custom scorers.
- **NVIDIA NCA Generative AI LLMs**: Data analysis and visualization; experimentation; data preprocessing and feature engineering.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
