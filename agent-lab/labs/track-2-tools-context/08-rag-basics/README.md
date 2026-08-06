# Lab 08 - RAG basics

## Goal

After this lab you can build a retrieval pipeline end to end: chunk documents, embed them with a deterministic local stub, search by cosine similarity, and generate an answer that is grounded in the retrieved passages and cites them.

## Prerequisites

Labs 00, 01, and 07. Concepts: vectors and cosine similarity, and `common/vectorstore.py`.

## Estimated time

60 to 90 minutes

## Background

Retrieval puts the right facts in front of the model at request time. It is the cheapest way to give a model knowledge it does not have, it updates the moment the source updates, and unlike fine tuning it leaves an audit trail: you can point at the passage an answer came from.

Chunking is the first real design decision. Chunks too small lose the context that makes a passage meaningful; chunks too large dilute the signal and waste tokens on text nobody asked for. Overlap between adjacent chunks keeps a sentence that straddles a boundary from becoming unretrievable. Lab 09 turns this into a measured sweep instead of a guess.

This lab uses a deterministic hash-based embedding stub rather than an embedding API. It is not semantically strong, and that is deliberate: it needs no account, no network, and no key, it returns the same vector for the same text every time, and it makes the pipeline mechanics testable. Every other part of the pipeline is exactly what you would build against a real embedding model.

Similarity search is cosine similarity over stored vectors, which is what `common/vectorstore.py` implements with numpy. Cosine compares direction rather than magnitude, which is what you want when documents differ in length. Persistence is a single sqlite3 file from the standard library.

Grounding is the part people skip. Retrieval that is not enforced in the prompt gives you a model that reads the passages and then answers from memory anyway. Tell it to answer only from the provided passages, to cite the chunk id for each claim, and to say it does not know when the passages do not cover the question.

A citation is only worth something if it is checkable. Return the retrieved chunk ids alongside the answer so a caller, a test, or a reviewer can confirm the cited passage actually says what the answer claims it says.

## Steps

1. Implement `chunk`: split text into overlapping windows of a target size, preferring sentence or paragraph boundaries over cutting mid-word.
2. Implement `embed`: a deterministic hash-based vector. Hash each token into a fixed number of dimensions, accumulate, and normalise. The same text must always produce the same vector.
3. Implement `build_store`: chunk every document, embed each chunk, and add it to a `VectorStore` with an id that identifies both the source document and the chunk index.
4. Implement `search`: embed the query and return the top k hits with their scores.
5. Implement `answer`: build a system prompt from the hits, instruct the model to cite chunk ids and to refuse when unsupported, and return both the answer and the ids that were retrieved.
6. Persist the store to sqlite3 under `data/`, reload it in a fresh process, and confirm search results are identical.

## Verification

```bash
pytest labs/track-2-tools-context/08-rag-basics/tests -v
```

The whole pipeline except the final generation is deterministic and runs offline. Passing means chunks respect the size and overlap settings, the same text always embeds to the same vector, a query retrieves the chunk that actually contains the answer, the store survives a save and load round trip unchanged, and a **separate process** reloading it ranks the chunks in the same order. That last one is only checked by actually crossing a process boundary: within one process the round trip passes even with the builtin `hash()`, whose salt changes from run to run.

## Going further

- Ask a question the corpus does not answer and confirm the model refuses instead of inventing a citation. An unfaithful citation is worse than no citation.
- Swap the hash embedding for token overlap scoring from lab 01 and compare which retrieves better on the same queries.
- Add a second document that contradicts the first and observe what the model does when both are retrieved.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: The retrieval half of the augmented LLM building block; grounding and citation.
- **Databricks Generative AI Engineer Associate**: Data preparation and chunking; application development including RAG.
- **NVIDIA NCA Generative AI LLMs**: Data preprocessing and feature engineering; Python libraries for LLMs.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
