"""Lab 09 - Retrieval quality (reference solution).

Retrieval measured instead of guessed at: recall at k against a labelled set,
a chunk-size sweep, a hybrid of keyword and vector scores tuned on that set,
and a reranking pass, all reported on the same queries so the strategies are
comparable.

Every ranking here breaks ties deterministically. A ranking that leaves ties
to the order documents happened to be declared in produces numbers that move
when the corpus is reordered, which makes the whole lab unmeasurable.
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
        "Opened software and clearance items cannot be returned. To start a "
        "return, print a prepaid label from the order page and drop the "
        "parcel at any carrier location. Return shipping is free for "
        "defective items and costs 6 dollars otherwise. Items must include "
        "all original accessories and packaging. A restocking fee of 15 "
        "percent applies to opened but undamaged electronics. Gift returns "
        "are refunded as store credit."
    ),
    "shipping-policy": (
        "Standard shipping takes 3 to 5 business days. Express shipping "
        "arrives the next business day for orders placed before 2pm. "
        "Orders over 50 dollars ship free with the standard option. We ship "
        "to all 50 states and to Canada. International orders outside North "
        "America are not supported at this time. Tracking numbers are "
        "emailed once the parcel leaves the warehouse. Signature on "
        "delivery is required for orders over 500 dollars. Rural addresses "
        "may add one extra transit day."
    ),
    "warranty-policy": (
        "Hardware carries a 12 month warranty covering manufacturing "
        "defects. Accidental damage is not covered. Warranty claims require "
        "the original receipt and the product serial number. Batteries and "
        "consumable parts are covered for 90 days only. An extended 36 "
        "month plan can be purchased within 30 days of the original order. "
        "Repairs usually complete in 10 business days. If a unit cannot be "
        "repaired we replace it with the same model or a current equivalent."
    ),
    "payment-methods": (
        "We accept credit cards, debit cards, and gift cards. Payment plans "
        "are available for orders over 200 dollars. Cheques and cash on "
        "delivery are not accepted for online orders. Cards are authorised "
        "at checkout and charged when the parcel ships. A payment plan "
        "splits the total into 4 interest free instalments taken every two "
        "weeks. Corporate purchase orders are accepted for approved "
        "business accounts with net 30 terms. We do not store full card "
        "numbers."
    ),
    "store-hours": (
        "The store is open from 9am to 6pm Monday through Saturday. On "
        "Sundays the store opens at noon and closes at 5pm. The store is "
        "closed on public holidays. The service counter closes 30 minutes "
        "before the store. Order pickup is available during all opening "
        "hours and takes about 10 minutes. During December the store stays "
        "open until 9pm on weekdays. Parking is free for the first 2 hours "
        "with a validated receipt."
    ),
    "price-match": (
        "We match any advertised price from an authorised retailer at the "
        "time of purchase. Price match requests need a link or printed "
        "advertisement. Marketplace sellers and auction sites are excluded. "
        "A match can be requested up to 14 days after purchase and the "
        "difference is refunded to the original payment method. Clearance, "
        "open box, and bundle prices are not eligible. Only one price match "
        "per item per customer. The competitor must have the item in stock "
        "at the advertised price."
    ),
}

# The labels name source documents, not chunk ids, because chunk ids change
# with every chunk size. Retrieved chunk ids are mapped back to their source
# document before scoring, so this list stays valid across the whole sweep.
#
# Twenty eight queries means one query is worth 1/28 = 0.036 of the score.
# Differences smaller than that are not results, and no amount of staring at
# the table will make them into results. Growing this list is the only way to
# resolve a smaller difference.
LABELLED_QUERIES: list[tuple[str, list[str]]] = [
    ("How many days do I have to return an item?", ["returns-policy"]),
    ("Can I return opened software?", ["returns-policy"]),
    ("When will my refund arrive?", ["returns-policy"]),
    ("How do I start a return?", ["returns-policy"]),
    ("Is there a restocking fee on opened electronics?", ["returns-policy"]),
    ("How are gift returns refunded?", ["returns-policy"]),
    ("How long does standard shipping take?", ["shipping-policy"]),
    ("Is there free shipping on large orders?", ["shipping-policy"]),
    ("Can my order arrive the next business day?", ["shipping-policy"]),
    ("Do you ship to Canada?", ["shipping-policy"]),
    ("Is a signature required for expensive orders?", ["shipping-policy"]),
    ("What does the warranty cover?", ["warranty-policy"]),
    ("Is accidental damage covered by the warranty?", ["warranty-policy"]),
    ("What do I need to make a warranty claim?", ["warranty-policy"]),
    ("How long are batteries covered?", ["warranty-policy"]),
    ("Can I buy an extended plan?", ["warranty-policy"]),
    ("Do you accept gift cards?", ["payment-methods"]),
    ("Are payment plans available?", ["payment-methods"]),
    ("Can I pay cash on delivery?", ["payment-methods"]),
    ("How many instalments does a payment plan have?", ["payment-methods"]),
    ("Do you take corporate purchase orders?", ["payment-methods"]),
    ("What time does the store open on Sunday?", ["store-hours"]),
    ("Is the store open on public holidays?", ["store-hours"]),
    ("When does the service counter close?", ["store-hours"]),
    ("Are the December hours different?", ["store-hours"]),
    ("Do you match a competitor's advertised price?", ["price-match"]),
    ("Are auction sites eligible for a price match?", ["price-match"]),
    ("How long after buying can I request a price match?", ["price-match"]),
]

# Sizes chosen so each one actually chunks the corpus differently. Two sizes
# that produce identical chunks are the same experiment run twice, and they
# make a sweep look like a plateau when nothing was measured at all.
SWEEP_SIZES: list[int] = [120, 200, 300, 400, 600]

# Retrieve a generous shortlist cheaply, then spend the careful pass on that
# shortlist only. Too short and reranking has nothing left to fix, because a
# document the cheap pass missed entirely can never be promoted.
SHORTLIST: int = 20


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


def build_store(documents: dict[str, str], *, size: int) -> VectorStore:
    """Chunk and embed every document into a VectorStore."""
    store = VectorStore()
    for chunk_id, text in build_chunks(documents, size=size):
        store.add(chunk_id, text, embed(text))
    return store


def document_of(chunk_id: str) -> str:
    """Map a chunk id like returns-policy#2 back to its source document."""
    return chunk_id.split("#")[0]


def keyword_score(query: str, text: str) -> float:
    """Fraction of query tokens present in the text, in [0, 1]."""
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0
    return len(query_tokens & tokenize(text)) / len(query_tokens)


def _stem(token: str) -> str:
    """Strip a common English suffix so refund and refunds match."""
    for suffix in ("ies", "es", "ing", "ed", "s"):
        if len(token) > len(suffix) + 2 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def careful_score(query: str, text: str) -> float:
    """Overlap after light suffix stripping, the reranker's scoring pass.

    This stands in for a cross-encoder: too slow for the whole corpus, worth
    it on a shortlist. It has to be a *different* function from
    keyword_score, or reranking inherits the exact blindness it is meant to
    repair. Plain overlap scores "When will my refund arrive?" at zero
    against every document, because the text says Refunds and arrives.
    """
    query_tokens = {_stem(token) for token in re.findall(r"\w+", query.lower())}
    if not query_tokens:
        return 0.0
    text_tokens = {_stem(token) for token in re.findall(r"\w+", text.lower())}
    return len(query_tokens & text_tokens) / len(query_tokens)


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


def keyword_ranked(query: str, chunks: list[tuple[str, str]]) -> list[str]:
    """Rank chunks by keyword overlap, dropping the ones that match nothing.

    Zero overlap is not a weak hit, it is not a hit, which is how an
    inverted index behaves. Keeping the zeros would return the entire corpus
    in dict order on every query, and a query where nothing matches would
    score by whichever document happened to be declared first. Remaining
    ties break on chunk id so the ranking cannot depend on corpus order.
    """
    scored = [
        (chunk_id, keyword_score(query, text))
        for chunk_id, text in chunks
        if keyword_score(query, text) > 0.0
    ]
    return [chunk_id for chunk_id, _ in sorted(scored, key=lambda pair: (-pair[1], pair[0]))]


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
        store = build_store(documents, size=size)
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


def hybrid_score(keyword: float, vector: float, alpha: float = 0.5) -> float:
    """Weighted combination of a keyword score and a vector score."""
    # Both inputs are clamped to [0, 1] so neither scale can dominate by
    # accident. Alpha 0 reproduces pure keyword and alpha 1 pure vector.
    keyword = min(max(keyword, 0.0), 1.0)
    vector = min(max(vector, 0.0), 1.0)
    return (1.0 - alpha) * keyword + alpha * vector


def hybrid_ranked(
    query: str,
    chunks: list[tuple[str, str]],
    vector_scores: dict[str, float],
    alpha: float,
) -> list[str]:
    """Rank chunks by the hybrid score, breaking ties on chunk id."""
    return [
        chunk_id
        for chunk_id, _ in sorted(
            chunks,
            key=lambda pair: (
                -hybrid_score(
                    keyword_score(query, pair[1]),
                    vector_scores.get(pair[0], 0.0),
                    alpha,
                ),
                pair[0],
            ),
        )
    ]


def rerank(query: str, hits: list[Any], *, keep: int = 3) -> list[Any]:
    """Reorder a shortlist with a more careful scoring pass."""
    # The output is a permutation of the input truncated to keep: silently
    # dropping or inventing a candidate would make the recall numbers
    # unexplainable. Ties fall back to the cheap score and then the id, so
    # the result never depends on the order the candidates arrived in.
    scored = sorted(
        hits,
        key=lambda hit: (-careful_score(query, hit.text), -hit.score, hit.id),
    )
    return scored[:keep]


def evaluate(
    documents: dict[str, str],
    queries: list[tuple[str, list[str]]],
    *,
    k: int = 3,
    size: int = 200,
    alpha: float = 0.5,
    shortlist: int = SHORTLIST,
) -> dict[str, float]:
    """Report recall at k for every strategy on the same labelled set."""
    chunks = build_chunks(documents, size=size)
    store = build_store(documents, size=size)

    per_strategy: dict[str, list[float]] = {
        "vector": [],
        "keyword": [],
        "hybrid": [],
        "reranked": [],
    }
    for query, relevant in queries:
        vector_hits = store.search(embed(query), len(chunks))
        vector_scores = {hit.id: hit.score for hit in vector_hits}
        ranked = (
            ("vector", [hit.id for hit in vector_hits]),
            ("keyword", keyword_ranked(query, chunks)),
            ("hybrid", hybrid_ranked(query, chunks, vector_scores, alpha)),
            ("reranked", [hit.id for hit in rerank(query, vector_hits[:shortlist], keep=k)]),
        )
        for name, ids in ranked:
            per_strategy[name].append(
                recall_at_k(_retrieved_documents(ids), relevant, k)
            )

    return {
        name: sum(values) / len(values) if values else 0.0
        for name, values in per_strategy.items()
    }


def tune_alpha(
    documents: dict[str, str],
    queries: list[tuple[str, list[str]]],
    alphas: list[float],
    *,
    k: int = 3,
    size: int = 200,
) -> dict[float, float]:
    """Report hybrid recall at k for each alpha, so the weight is measured.

    Alpha is a knob to set on a labelled set, not a constant to copy from
    someone else's blog post. The interesting outcome is an interior
    optimum: if some middle alpha beats both alpha 0 and alpha 1, the two
    signals really are failing on different queries.
    """
    return {
        alpha: evaluate(documents, queries, k=k, size=size, alpha=alpha)["hybrid"]
        for alpha in alphas
    }


def split_queries(
    queries: list[tuple[str, list[str]]],
) -> tuple[list[tuple[str, list[str]]], list[tuple[str, list[str]]]]:
    """Split the labelled set into a half to tune on and a half to report on.

    Picking the best of five alphas and then reporting that alpha's score on
    the same queries reports the best of five tries, which is optimistic by
    construction. Every knob is chosen on the tuning half and the number
    that gets quoted comes from the held-out half.

    Alternating keeps both halves covering every document, because the list
    is grouped by document. Splitting is not free: two halves of fourteen
    resolve 1/14 each instead of 1/28, so the honest cost of a held-out set
    is that you need a bigger labelled set to begin with.
    """
    tuning = [pair for index, pair in enumerate(queries) if index % 2 == 0]
    holdout = [pair for index, pair in enumerate(queries) if index % 2 == 1]
    return tuning, holdout


def main() -> int:
    """Tune every knob on one half of the labelled set, report on the other."""
    # k=1 asks each strategy to put the right document first, which is a
    # stricter question than k=3 and makes the differences visible on a
    # corpus this small.
    tuning, holdout = split_queries(LABELLED_QUERIES)
    resolution = 1.0 / len(tuning)
    print(
        f"{len(LABELLED_QUERIES)} labelled queries split into {len(tuning)} for "
        f"tuning and {len(holdout)} held out, so one query is worth "
        f"{resolution:.3f} in either half"
    )

    print("\nchunk size sweep on the tuning half (recall at 1)")
    sweep = sweep_chunk_sizes(CORPUS, tuning, SWEEP_SIZES, k=1)
    for size, recall in sweep.items():
        count = len(build_chunks(CORPUS, size=size))
        print(f"  size {size:>4}  {count:>3} chunks  {recall:.3f}")
    spread = max(sweep.values()) - min(sweep.values())
    print(f"  spread {spread:.3f}, which is {spread / resolution:.1f} queries")
    # The spread is inside the resolution of the set, so there is nothing here
    # to choose between. Keeping the documented default is the honest reading;
    # picking the argmax of a flat curve is fitting noise.
    print("  spread is within one query, so chunk size is not the lever here")

    print("\nalpha tuning on the tuning half (hybrid recall at 1)")
    tuned = tune_alpha(CORPUS, tuning, [0.0, 0.25, 0.5, 0.75, 1.0], k=1)
    for alpha, recall in tuned.items():
        print(f"  alpha {alpha:.2f}  {recall:.3f}")
    best = max(tuned, key=lambda alpha: tuned[alpha])
    print(f"  chose alpha {best:.2f}")

    print(f"\nstrategy comparison at alpha {best:.2f} (recall at 1)")
    on_tuning = evaluate(CORPUS, tuning, k=1, alpha=best)
    on_holdout = evaluate(CORPUS, holdout, k=1, alpha=best)
    print(f"  {'':<9} {'tuning':>8} {'held out':>10}")
    for name in on_holdout:
        print(f"  {name:<9} {on_tuning[name]:>8.3f} {on_holdout[name]:>10.3f}")

    # Two different things are visible in that table. The hybrid gap is the
    # cost of having chosen alpha on the tuning half: quote the held-out
    # number. The gaps on strategies that were never tuned are pure split
    # noise, and if they are the larger of the two, the labelled set is too
    # small for either number to be trusted on its own.
    print(f"\n  hybrid, tuned then held out: {on_tuning['hybrid'] - on_holdout['hybrid']:+.3f}")
    untuned = max(
        abs(on_tuning[name] - on_holdout[name])
        for name in on_holdout
        if name != "hybrid"
    )
    print(f"  largest gap on an untuned strategy: {untuned:.3f} (split noise)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
