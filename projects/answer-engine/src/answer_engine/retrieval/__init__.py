"""Hybrid retrieval — keyword overlap plus dense hash embeddings.

Purpose
    Build an in-memory corpus index and retrieve a cheap shortlist of passages.

Why
    Case 02 (and labs 08/09) treat hybrid retrieval as the agreed first ranking
    stage: exact terms via keyword, paraphrase-ish match via vectors. Staging
    spends little compute on many candidates.

Trade-offs
    Hash embeddings are not semantic; they are deterministic and offline. A real
    embedding API would retrieve better and break the no-network lab constraint.
    Stopword filtering reduces false matches from "what/is/the" but can drop
    meaningful short tokens.

Edges
    Empty documents yield no passages. Queries that are only stopwords score 0
    on keyword and rely on (weak) dense scores until the pipeline abstain gate.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from common.vectorstore import VectorStore
from answer_engine.paths import CORPUS_DIR


@dataclass(frozen=True)
class Passage:
    """One retrieved chunk with the scores attached along the pipeline.

    Purpose
        Carry text plus scoring fields so later stages do not re-parse the store.

    Why
        Frozen dataclass keeps ranking steps pure: each stage returns new
        Passage values instead of mutating shared state.

    Trade-offs
        Copying fields on each stage is verbose but makes traces easy to read.

    Edges
        Scores default to 0.0 until a stage fills them in.
    """

    id: str
    text: str
    doc_id: str
    keyword_score: float = 0.0
    vector_score: float = 0.0
    hybrid_score: float = 0.0
    careful_score: float = 0.0


STOPWORDS = frozenset(
    {
        "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "is", "are",
        "was", "were", "be", "been", "what", "when", "where", "who", "whom", "which",
        "how", "why", "do", "does", "did", "can", "could", "should", "would", "from",
        "with", "as", "by", "at", "it", "its", "this", "that", "these", "those",
        "there", "their", "we", "you", "i", "my", "our", "your",
    }
)


def tokenize(text: str) -> set[str]:
    """Return content tokens for scoring.

    Purpose
        Shared tokenization for keyword, careful, and embedding bags.

    Why
        Dropping stopwords prevents out-of-corpus questions from matching on
        "what/is/the" alone.

    Trade-offs
        A fixed English stop list is incomplete and language-specific.

    Edges
        Single-character tokens are dropped. Empty input yields an empty set.
    """
    return {t for t in re.findall(r"\w+", text.lower()) if t not in STOPWORDS and len(t) > 1}


def embed(text: str, *, dim: int = 256) -> np.ndarray:
    """Deterministic hash bag-of-tokens embedding (lab 08 stub).

    Purpose
        Map text to a unit vector without a network embedding API.

    Why
        Same vector for the same text across processes (md5, not salted hash).

    Trade-offs
        Not semantic. Good enough to teach hybrid fusion and keep tests offline.

    Edges
        All-stopword text becomes a zero vector; cosine with it is guarded by
        the vector store's epsilon norm.
    """
    vector = np.zeros(dim, dtype=np.float32)
    for token in tokenize(text):
        digest = hashlib.md5(token.encode("utf-8")).digest()
        vector[int.from_bytes(digest[:4], "big") % dim] += 1.0
    norm = float(np.linalg.norm(vector))
    if norm > 0.0:
        vector /= norm
    return vector


def chunk(text: str, *, size: int = 280, overlap: int = 40) -> list[str]:
    """Split a document into overlapping windows.

    Purpose
        Give retrieval units smaller than whole files.

    Why
        Citations need passage ids; whole-doc retrieval is too coarse for
        grounding checks on a multi-topic corpus.

    Trade-offs
        Fixed character windows ignore sentence boundaries (simpler than lab 09
        sentence-aware chunking). Overlap can duplicate facts across chunks.

    Edges
        Empty/whitespace input returns []. Last window may be shorter than size.
    """
    text = " ".join(text.split())
    if not text:
        return []
    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        pieces.append(text[start:end])
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return pieces


def load_documents(corpus_dir: Path | None = None) -> dict[str, str]:
    """Load ``*.md`` files keyed by stem.

    Purpose
        Provide the local knowledge base for the engine.

    Why
        Stem ids become citation document ids (``grounding#0`` → ``grounding``).

    Trade-offs
        Only markdown; no HTML/PDF pipeline.

    Edges
        Missing directory raises from Path.glob via empty dict if dir exists empty.
    """
    root = corpus_dir or CORPUS_DIR
    return {
        path.stem: path.read_text(encoding="utf-8")
        for path in sorted(root.glob("*.md"))
    }


def keyword_score(query: str, text: str) -> float:
    """Jaccard-like overlap of content tokens: |q ∩ t| / |q|.

    Purpose
        Exact-term signal for hybrid fusion.

    Why
        Strong when the user and the doc share vocabulary (lab 09 keyword path).

    Trade-offs
        Biased toward short queries. No IDF, so common content words still weigh
        equally.

    Edges
        Returns 0.0 if either side has no content tokens after stopword filter.
    """
    q = tokenize(query)
    t = tokenize(text)
    if not q or not t:
        return 0.0
    return len(q & t) / len(q)


def careful_score(query: str, text: str) -> float:
    """Denser content-token overlap for the rerank stage.

    Purpose
        Re-score a shortlist with a slightly different formula than keyword_score.

    Why
        Lab 09 teaches that the careful pass must not reuse the cheap scorer
        blindly. Counting occurrences in the passage (not only set overlap)
        rewards denser matches.

    Trade-offs
        Still lexical, not a cross-encoder. Good shape, weak semantics.

    Edges
        Returns 0.0 when query or passage has no content tokens.
    """
    q_tokens = list(tokenize(query))
    t_tokens = [
        t for t in re.findall(r"\w+", text.lower()) if t not in STOPWORDS and len(t) > 1
    ]
    if not q_tokens or not t_tokens:
        return 0.0
    q_set = set(q_tokens)
    overlap = sum(1 for tok in t_tokens if tok in q_set)
    return overlap / (len(q_tokens) + 0.5 * len(t_tokens))


def hybrid_score(keyword: float, vector: float, alpha: float = 0.5) -> float:
    """Linear fuse keyword and dense scores.

    Purpose
        Single ranking key for the cheap shortlist.

    Why
        Alpha is the standard teaching knob from lab 09.

    Trade-offs
        Untuned alpha=0.5. Production would sweep alpha on labelled queries.

    Edges
        Alpha outside [0, 1] is allowed but not validated (caller responsibility).
    """
    return alpha * keyword + (1.0 - alpha) * vector


@dataclass
class CorpusIndex:
    """In-memory documents, passages, and vector store.

    Purpose
        One object the rest of the pipeline reads from.

    Why
        Building once per process avoids re-chunking on every question.

    Trade-offs
        Entire corpus in RAM. Fine for the teaching corpus; not for web scale.
    """

    documents: dict[str, str]
    passages: list[Passage]
    store: VectorStore

    @classmethod
    def build(cls, documents: dict[str, str] | None = None) -> "CorpusIndex":
        """Chunk, embed, and index documents.

        Purpose
            Construct a ready-to-search index.

        Why
            Passage ids encode ``{doc_id}#{index}`` so citations map back to docs.

        Trade-offs
            Rebuild is full, not incremental.

        Edges
            ``documents=None`` loads from disk. Empty dict yields empty store.
        """
        docs = documents if documents is not None else load_documents()
        store = VectorStore()
        passages: list[Passage] = []
        for doc_id, text in docs.items():
            for index, piece in enumerate(chunk(text)):
                pid = f"{doc_id}#{index}"
                store.add(pid, piece, embed(piece))
                passages.append(Passage(id=pid, text=piece, doc_id=doc_id))
        return cls(documents=docs, passages=passages, store=store)


def hybrid_retrieve(
    index: CorpusIndex,
    query: str,
    *,
    shortlist: int = 12,
    alpha: float = 0.5,
) -> list[Passage]:
    """Return the top hybrid-scoring passages.

    Purpose
        Cheap first cut before careful reranking.

    Why
        Case 02 shape: evaluate many candidates cheaply, few carefully.

    Trade-offs
        Scores every passage (O(n)). Fine at teaching scale; needs inverted
        index / ANN at web scale.

    Edges
        shortlist <= 0 returns []. Ties break on passage id for stability.
    """
    vector_hits = {
        hit.id: hit.score for hit in index.store.search(embed(query), k=len(index.passages))
    }
    scored: list[Passage] = []
    for passage in index.passages:
        kw = keyword_score(query, passage.text)
        vec = float(vector_hits.get(passage.id, 0.0))
        scored.append(
            Passage(
                id=passage.id,
                text=passage.text,
                doc_id=passage.doc_id,
                keyword_score=kw,
                vector_score=vec,
                hybrid_score=hybrid_score(kw, vec, alpha),
            )
        )
    scored.sort(key=lambda p: (-p.hybrid_score, p.id))
    return scored[:shortlist]
