# Grounding and citations

Grounding means every claim in an answer is tied to retrieved evidence.
Citations should be assembled into the prompt before generation, so attribution
is a constraint on writing rather than a reconstruction afterwards.

The characteristic failure of an answer engine is a fluent answer that outruns
its evidence. Read-only systems cannot fix that with a verification loop when
the latency budget forbids a second pass.
