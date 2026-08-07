"""Intent parsing — first stage of the answer-engine workflow.

Purpose
    Label the question coarsely and lightly rewrite the retrieval query.

Why
    Case 02 reconstructions start with query-intent parsing. A mistake here
    propagates through retrieval and ranking; there is no later verification
    loop to catch a misread question.

Trade-offs
    Keyword rules are cheap and deterministic, but brittle. A small classifier
    model would be more accurate and more expensive, and would need its own
    eval. This project keeps rules so the stage stays offline-testable.

Edges
    - Ambiguous questions default to ``factual``.
    - Overlapping cues (e.g. "how do X and Y differ") prefer comparison because
      that branch is checked first.
"""

from __future__ import annotations

import re


def parse_intent(question: str) -> str:
    """Classify a question as factual, comparison, or how_to.

    Purpose
        Produce a stable intent label for downstream query rewriting.

    Why
        Staging needs a signal before retrieval. Intent is that signal without
        calling the model yet (latency budget).

    Trade-offs
        Regex over a closed set of cues vs. an LLM classifier. Regex wins on
        cost and determinism; loses on paraphrase coverage.

    Edges
        Empty or whitespace-only input still returns ``factual``.
        Unknown phrasings fall through to ``factual`` rather than erroring.
    """
    text = question.lower().strip()
    if re.search(r"\b(differ|difference|vs|versus|compare|between)\b", text):
        return "comparison"
    if re.search(r"\b(how (do|to|should)|steps|way to)\b", text):
        return "how_to"
    return "factual"


def retrieval_query(question: str, intent: str) -> str:
    """Rewrite the question so hybrid retrieval sees intent-shaped terms.

    Purpose
        Bias keyword/dense overlap toward passages that match the intent.

    Why
        Without a rewrite, comparison questions under-match documents that say
        "difference" but not "vs". Prefixing a few terms is enough for a tiny
        corpus.

    Trade-offs
        Query expansion can drag in unrelated docs on a large corpus. Here the
        corpus is small, so the bias helps more than it hurts.

    Edges
        Unknown intent labels are treated as no rewrite (return question as-is).
    """
    if intent == "comparison":
        return f"compare difference {question}"
    if intent == "how_to":
        return f"how to steps {question}"
    return question
