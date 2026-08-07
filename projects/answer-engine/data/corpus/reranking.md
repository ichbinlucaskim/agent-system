# Reranking stages

Staged reranking runs cheap methods over many candidates and expensive methods
over few. A quality threshold at a late stage can discard a weak candidate set
and restart retrieval when too few passages clear the bar.

Do not treat any one public reconstruction of a commercial reranker stack as
ground truth. The shape that matters is hybrid retrieval, then staged ranking,
then synthesis constrained to evidence.
