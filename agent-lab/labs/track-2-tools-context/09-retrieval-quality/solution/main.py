"""Lab 09 - Retrieval quality (reference solution).

Retrieval measured instead of guessed at: recall at k against a labelled set,
a chunk-size sweep, a hybrid of keyword and vector scores, and a reranking
pass, all reported on the same queries so the strategies are comparable.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

import numpy as np

from common.vectorstore import SearchHit, VectorStore

CORPUS: dict[str, str] = {
    "returns-policy": (
        "Returns are accepted within 30 days of delivery. Refunds are issued "
        "to the original payment method within 5 business days of receipt. "
        "Opened software and clearance items cannot be returned."
    ),
    "shipping-policy": (
        "Standard shipping takes 3 to 5 business days. Express shipping "
        "arrives the next business day for orders placed before 2pm. "
        "Orders over 50 dollars ship free with the standard option."
    ),
    "warranty-policy": (
        "Hardware carries a 12 month warranty covering manufacturing defects. "
        "Accidental damage is not covered. Warranty claims require the "
        "original receipt and the product serial number."
    ),
    "payment-methods": (
        "We accept credit cards, debit cards, and gift cards. Payment plans "
        "are available for orders over 200 dollars. Cheques and cash on "
        "delivery are not accepted for online orders."
    ),
    "store-hours": (
        "The store is open from 9am to 6pm Monday through Saturday. On "
        "Sundays the store opens at noon and closes at 5pm. The store is "
        "closed on public holidays."
    ),
    "price-match": (
        "We match any advertised price from an authorised retailer at the "
        "time of purchase. Price match requests need a link or printed "
        "advertisement. Marketplace sellers and auction sites are excluded."
    ),
}

# The labels name source documents, not chunk ids, because chunk ids change
# with every chunk size. Retrieved chunk ids are mapped back to their source
# document before scoring, so this list stays valid across the whole sweep.
LABELLED_QUERIES: list[tuple[str, list[str]]] = [
    ("How many days do I have to return an item?", ["returns-policy"]),
    ("Can I return opened software?", ["returns-policy"]),
    ("When will my refund arrive?", ["returns-policy"]),
    ("How long does standard shipping take?", ["shipping-policy"]),
    ("Is there free shipping on large orders?", ["shipping-policy"]),
    ("Can my order arrive the next business day?", ["shipping-policy"]),
    ("What does the warranty cover?", ["warranty-policy"]),
    ("Is accidental damage covered by the warranty?", ["warranty-policy"]),
    ("What do I need to make a warranty claim?", ["warranty-policy"]),
    ("Do you accept gift cards?", ["payment-methods"]),
    ("Are payment plans available?", ["payment-methods"]),
    ("Can I pay cash on delivery?", ["payment-methods"]),
    ("What time does the store open on Sunday?", ["store-hours"]),
    ("Is the store open on public holidays?", ["store-hours"]),
    ("Do you match a competitor's advertised price?", ["price-match"]),
    ("Are auction sites eligible for a price match?", ["price-match"]),
]


# Lab directories are not importable packages, so the small pieces of lab 08
# that this lab measures are restated here.
def tokenize(text: str) -> set[str]:
    """Lowercase a string and return its set of word tokens."""
    return set(re.findall(r"\w+", text.lower()))


def embed(text: str, *, dim: int = 256) -> np.ndarray:
    """Deterministic hash-based embedding stub, identical to lab 08."""
    vector = np.zeros(dim, dtype=np.float32)
    for token in re.findall(r"\w+", text.lower()):
        digest = hashlib.md5(token.encode("utf-8")).digest()
        vector[int.from_bytes(digest[:4], "big") % dim] += 1.0
    norm = float(np.linalg.norm(vector))
    if norm > 0.0:
        vector /= norm
    return vector


def chunk(text: str, *, size: int = 200, overlap: int = 40) -> list[str]:
    """Split text into overlapping windows, identical in spirit to lab 08."""
    if overlap >= size:
        raise ValueError(f"overlap ({overlap}) must be smaller than size ({size})")
    text = " ".join(text.split())
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            window = text[start:end]
            cut = max(window.rfind(". "), window.rfind("? "), window.rfind(" "))
            if cut > 0:
                end = start + cut + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        next_start = max(end - overlap, start + 1)
        boundary = text.rfind(" ", start + 1, next_start + 1) + 1
        start = boundary if boundary > start else next_start
    return chunks


def build_chunks(documents: dict[str, str], *, size: int) -> list[tuple[str, str]]:
    """Chunk every document into (chunk_id, text) pairs."""
    return [
        (f"{document_id}#{index}", piece)
        for document_id, text in documents.items()
        for index, piece in enumerate(chunk(text, size=size))
    ]


def document_of(chunk_id: str) -> str:
    """Map a chunk id like returns-policy#2 back to its source document."""
    return chunk_id.split("#")[0]


def keyword_score(query: str, text: str) -> float:
    """Fraction of query tokens present in the text, in [0, 1]."""
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0
    return len(query_tokens & tokenize(text)) / len(query_tokens)


def recall_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    """Fraction of relevant ids that appear in the top k retrieved ids."""
    # Recall with nothing relevant is undefined. Returning 0.0 rather than
    # 1.0 keeps an unlabelled query from inflating the average.
    if not relevant_ids:
        return 0.0
    top = set(retrieved_ids[:k])
    return sum(1 for relevant in relevant_ids if relevant in top) / len(relevant_ids)


def _retrieved_documents(chunk_ids: list[str]) -> list[str]:
    """Map ranked chunk ids to source documents, deduplicated in rank order."""
    seen: list[str] = []
    for chunk_id in chunk_ids:
        document = document_of(chunk_id)
        if document not in seen:
            seen.append(document)
    return seen


def sweep_chunk_sizes(
    documents: dict[str, str],
    queries: list[tuple[str, list[str]]],
    sizes: list[int],
    *,
    k: int = 3,
) -> dict[int, float]:
    """Rebuild the store at each chunk size and report mean recall at k."""
    results: dict[int, float] = {}
    for size in sizes:
        # Only the chunk size varies; the queries and labels are held fixed,
        # otherwise the numbers would not be comparable across sizes.
        store = VectorStore()
        for chunk_id, text in build_chunks(documents, size=size):
            store.add(chunk_id, text, embed(text))
        recalls = [
            recall_at_k(
                _retrieved_documents([hit.id for hit in store.search(embed(query), k)]),
                relevant,
                k,
            )
            for query, relevant in queries
        ]
        results[size] = sum(recalls) / len(recalls) if recalls else 0.0
    return results


def hybrid_score(keyword_score: float, vector_score: float, alpha: float = 0.5) -> float:
    """Weighted combination of a keyword score and a vector score."""
    # Both inputs are clamped to [0, 1] so neither scale can dominate by
    # accident. Alpha 0 reproduces pure keyword and alpha 1 pure vector.
    keyword = min(max(keyword_score, 0.0), 1.0)
    vector = min(max(vector_score, 0.0), 1.0)
    return (1.0 - alpha) * keyword + alpha * vector


def rerank(query: str, hits: list[Any], *, keep: int = 3) -> list[Any]:
    """Reorder a shortlist with a more careful scoring pass."""
    # The careful pass here is exact keyword overlap, standing in for a
    # cross-encoder. The output is a permutation of the input truncated to
    # keep: silently dropping or inventing a candidate would make the recall
    # numbers unexplainable.
    scored = sorted(
        enumerate(hits),
        key=lambda pair: (-keyword_score(query, pair[1].text), pair[0]),
    )
    return [hit for _, hit in scored[:keep]]


def evaluate(
    documents: dict[str, str],
    queries: list[tuple[str, list[str]]],
    *,
    k: int = 3,
) -> dict[str, float]:
    """Report recall at k for every strategy on the same labelled set."""
    chunks = build_chunks(documents, size=200)
    store = VectorStore()
    for chunk_id, text in chunks:
        store.add(chunk_id, text, embed(text))

    per_strategy: dict[str, list[float]] = {
        "vector": [],
        "keyword": [],
        "hybrid": [],
        "reranked": [],
    }
    for query, relevant in queries:
        vector_hits = store.search(embed(query), len(chunks))
        vector_ranked = [hit.id for hit in vector_hits]
        keyword_ranked = [
            chunk_id
            for chunk_id, _ in sorted(
                chunks, key=lambda pair: -keyword_score(query, pair[1])
            )
        ]
        vector_scores = {hit.id: hit.score for hit in vector_hits}
        hybrid_ranked = [
            chunk_id
            for chunk_id, _ in sorted(
                chunks,
                key=lambda pair: -hybrid_score(
                    keyword_score(query, pair[1]), vector_scores.get(pair[0], 0.0)
                ),
            )
        ]
        # Retrieve a generous shortlist cheaply, then spend the careful pass
        # on that shortlist only. That asymmetry is the point of reranking.
        reranked = [hit.id for hit in rerank(query, vector_hits[: 4 * k], keep=k)]

        for name, ranked in (
            ("vector", vector_ranked),
            ("keyword", keyword_ranked),
            ("hybrid", hybrid_ranked),
            ("reranked", reranked),
        ):
            per_strategy[name].append(
                recall_at_k(_retrieved_documents(ranked), relevant, k)
            )

    return {
        name: sum(values) / len(values) if values else 0.0
        for name, values in per_strategy.items()
    }


def main() -> int:
    """Run the sweep and the strategy comparison and print both tables."""
    # k=1 asks each strategy to put the right document first, which is a
    # stricter question than k=3 and makes the differences visible on a
    # corpus this small.
    sizes = [100, 200, 400]
    print(f"chunk size sweep (recall at 1, {len(LABELLED_QUERIES)} queries)")
    for size, recall in sweep_chunk_sizes(CORPUS, LABELLED_QUERIES, sizes, k=1).items():
        print(f"  size {size:>4}  {recall:.2f}")

    print("\nstrategy comparison (recall at 1, same queries)")
    for name, recall in evaluate(CORPUS, LABELLED_QUERIES, k=1).items():
        print(f"  {name:<9} {recall:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
