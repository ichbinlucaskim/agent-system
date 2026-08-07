# Prompt assembly

Prompt assembly gathers the ranked passages, embeds citation markers such as
[doc#0] next to each passage, and only then calls the model. Synthesis
instructions tell the model to answer only from those passages and to cite
them.

If sources are summarized away before drafting, attribution becomes a separate
reconstruction problem. Keeping sources until generation time is the stronger
default when latency allows the passages to fit.
