"""Lab 09 - Retrieval quality (starter).

Goal: Measure retrieval instead of guessing at it: compute recall at k against a labelled set, sweep chunk sizes, combine keyword and vector scores into a hybrid ranking, and add a reranking pass.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-2-tools-context/09-retrieval-quality/tests -v
"""

from __future__ import annotations

from typing import Any


def recall_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    """Fraction of relevant ids that appear in the top k retrieved ids."""
    # TODO: step 2. Compare only the first k retrieved ids. An empty relevant list is undefined rather than perfect: return 0.0 and document the choice.
    raise NotImplementedError


def sweep_chunk_sizes(documents: dict[str, str], queries: list[tuple[str, list[str]]], sizes: list[int], *, k: int = 3) -> dict[int, float]:
    """Rebuild the store at each chunk size and report mean recall at k."""
    # TODO: step 3. Hold the queries and labels fixed and vary only the size, or the comparison means nothing.
    raise NotImplementedError


def hybrid_score(keyword_score: float, vector_score: float, alpha: float = 0.5) -> float:
    """Weighted combination of a keyword score and a vector score."""
    # TODO: step 4. Normalise both inputs to the same range first. alpha of 0 must reproduce pure keyword and alpha of 1 pure vector.
    raise NotImplementedError


def rerank(query: str, hits: list[Any], *, keep: int = 3) -> list[Any]:
    """Reorder a shortlist with a more careful scoring pass."""
    # TODO: step 5. Return a permutation of the input, truncated to keep. Dropping a candidate silently makes the recall numbers unexplainable.
    raise NotImplementedError


def evaluate(documents: dict[str, str], queries: list[tuple[str, list[str]]], *, k: int = 3) -> dict[str, float]:
    """Report recall at k for every strategy on the same labelled set."""
    # TODO: step 6. Return one entry per strategy: vector, keyword, hybrid, reranked. One table is what makes the strategies comparable.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
