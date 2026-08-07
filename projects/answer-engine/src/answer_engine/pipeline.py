"""End-to-end answer-engine workflow (architecture root).

Purpose
    Wire intent → retrieve/rank → abstain-or-synthesize into one function that
    packaging adapters call.

Why
    Case 02 is a fixed pipeline, not an agent. Keeping a single ``answer_question``
    core prevents CLI/HTTP from drifting (lab 18 packaging lesson).

Trade-offs
    Abstain rules (keyword_score > 0 plus score floor) are conservative: they
    block dense-only noise but may abstain on paraphrase-only matches when the
    hash embedding fails. Acceptable for a teaching corpus.

Edges
    Empty / oversized questions raise ValueError before any retrieval.
"""

from __future__ import annotations

from typing import Any, Callable

from answer_engine.intent import parse_intent, retrieval_query
from answer_engine.packaging.config import Config
from answer_engine.ranking import rank_with_failsafe
from answer_engine.retrieval import CorpusIndex
from answer_engine.synthesis import (
    ABSTAIN,
    assemble_prompt,
    document_of,
    extract_citations,
    synthesize,
)


def answer_question(
    question: str,
    index: CorpusIndex,
    config: Config,
    *,
    complete_fn: Callable[..., Any] | None = None,
    offline: bool = False,
) -> dict[str, Any]:
    """Run the full read-only answering workflow for one question.

    Purpose
        Return answer, passages, citations, and rank trace for one query.

    Why
        One core keeps adapters thin. Offline/live shares the same retrieval
        path so eval measures grounding, not packaging differences.

    Trade-offs
        ``abstained`` is detected by prefix of ABSTAIN text—fragile if the live
        model paraphrases refusal. Offline path is stable.

    Edges
        No strong passages → ABSTAIN without calling the model.
        Dense hit without keyword overlap is dropped (out-of-corpus guard).
    """
    question = question.strip()
    if not question:
        raise ValueError("question is empty")
    if len(question) > config.max_chars:
        raise ValueError(
            f"question is {len(question)} characters, limit is {config.max_chars}"
        )

    intent = parse_intent(question)
    query = retrieval_query(question, intent)
    broadened = f"{intent} {question}"

    passages, rank_trace = rank_with_failsafe(
        index,
        query,
        keep=config.top_k,
        min_score=config.min_score,
        broadened_query=broadened,
    )

    strong = [
        p
        for p in passages
        if p.keyword_score > 0.0
        and (p.careful_score >= config.min_score or p.hybrid_score >= config.min_score)
    ]
    use_offline = offline or complete_fn is None
    if not strong:
        answer = ABSTAIN
        system, _ = assemble_prompt(question, [])
        citations: list[str] = []
    else:
        answer = synthesize(
            question,
            strong,
            model=config.model,
            complete_fn=complete_fn,
            offline=use_offline,
        )
        citations = extract_citations(answer)
        system, _ = assemble_prompt(question, strong)

    cited_docs = sorted({document_of(c) for c in citations})
    return {
        "question": question,
        "intent": intent,
        "retrieval_query": query,
        "answer": answer,
        "passages": [
            {
                "id": p.id,
                "doc_id": p.doc_id,
                "hybrid_score": p.hybrid_score,
                "careful_score": p.careful_score,
                "text": p.text,
            }
            for p in strong
        ],
        "citations": citations,
        "cited_docs": cited_docs,
        "abstained": answer.startswith("I do not know"),
        "rank_trace": rank_trace,
        "prompt_system_preview": system[:240],
    }
