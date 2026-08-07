# Hybrid retrieval

Hybrid retrieval combines a keyword signal such as BM25-style token overlap
with a dense embedding similarity score. Keyword matching is strong on exact
terms. Dense vectors help when the query and document use different words for
the same idea.

A typical pattern retrieves a generous shortlist cheaply, then spends a more
careful reranker only on that shortlist. Staging is how you spend a tight
latency budget unevenly.
