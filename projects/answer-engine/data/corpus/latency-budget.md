# Answer engine latency

An answer engine is organized around an interactive latency budget. There is
usually no post-generation verification loop. Correctness is forced by putting
the right evidence in front of the model on the first attempt.

Because the action space is read-only, there is nothing to approve. Design
effort moves from permission gates to retrieval and ranking quality.
