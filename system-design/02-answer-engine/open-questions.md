# Open questions - 02 Answer engine

Two of the twelve dimensions are empty and the rest rest on reconstruction. This
case has more open questions than any filled case in the library, and the first
one is whether the case should be believed at all.

## Unknown mechanism

- **Is any of this correct?** No first-party description exists in our material,
  so the entire architecture rests on two outside accounts that disagree with
  each other. This matters more than any individual gap below: a reader could
  reasonably conclude that the shape is right and every detail is wrong. Any
  first-party publication would answer it, and until one exists this case should
  be treated as a study of the archetype and not of the product.

- **Does the restart fail-safe exist?** ziptie.dev describes a quality threshold
  at the third reranking layer with a fail-safe that discards the candidate set
  and restarts retrieval. stackmatix.com does not mention it. This matters
  because it is the difference between a strictly feed-forward pipeline and one
  with a loop, which changes the answer to dimensions 8 and 9 entirely. A
  first-party statement, or observed behavior showing repeated retrieval on
  sparse queries, would answer it.

- **What are the three ranking stages actually made of?** Both sources say
  three and describe different threes. This matters for anyone trying to learn
  from the design rather than merely from its shape, and it is the reason
  `README.md` recommends stealing the shape and not the internals.

- **How is conversational state handled?** Dimension 7 is empty. Neither source
  describes whether a follow-up question re-retrieves from scratch, reuses the
  prior candidate set, or carries any personalization. This matters because it
  determines whether the latency budget applies per question or per session.

- **How is the system evaluated?** Dimension 11 is empty. Outside reconstruction
  works from outputs, so evaluation is invisible to it by construction. This
  matters because grounding is the correctness mechanism in this archetype and
  we have no idea how grounding is measured.

- **What happens when retrieval genuinely finds nothing useful?** The fail-safe
  restarts retrieval, and no source describes what happens if the restart also
  fails. This matters because refusing to answer is the correct behavior and is
  also the behavior a product is under the most pressure not to adopt.

## Unknown magnitude

- **What is the latency budget?** Dimension 12 is built on the claim that the
  budget is hard, and we have no number. This matters because the entire
  argument for staged reranking is a response to a constraint we can only
  describe qualitatively.

- **How many candidates enter and survive each stage?** Staged reranking is
  interesting precisely because the candidate set shrinks while the cost per
  candidate rises. Without any of those figures the description is a shape
  rather than an engineering account.

- **How often does the fail-safe fire, assuming it exists?** A recovery path that
  runs on one query in ten thousand and one that runs on one in five are
  different designs with the same diagram.

## Disputed between sources

- **The composition of the reranking stack.** ziptie.dev describes multi-layer ML
  ranking with a three-tier reranker and a quality threshold at the third layer.
  stackmatix.com describes BM25 plus embedding retrieval, then cross-encoder
  reranking, then an ML reranker using entity and authority signals. Both are
  recorded in `architecture.md` and neither is adopted. What would answer it: a
  first-party description, or an independent third reconstruction that agrees
  with one of them in detail rather than in outline.

- **Whether the pipeline contains a loop.** Covered above under unknown
  mechanism, and it is a genuine source disagreement rather than a gap. ziptie.dev
  implies iteration; stackmatix.com describes a feed-forward stack.

- **Whether query intent parsing is a distinct stage.** ziptie.dev names it as
  the first stage. stackmatix.com's account begins at retrieval. This may be a
  difference in scope rather than in substance, and we cannot tell which.

## Deliberately out of scope

- **How to rank well in an answer engine.** This is what most of the available
  T2 material is actually about, and it is a marketing discipline rather than a
  systems one. It is also the reason to read that material with care.

- **Whether answer engines are good for the web.** A real question and not an
  architecture question.

- **Comparison with other answer engines.** Would require sourced material on
  each, and we have partial material on one.
