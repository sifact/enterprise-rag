# prompt.py

Builds the messages sent to the answer model.

- Retrieved passages become numbered sources, each wrapped in `<source n="..." doc="..." title="..." where="...">…</source>` tags so the model can cite them and can't mistake them for instructions.
- The system prompt says sources are untrusted data and that any instruction, role claim or formatting demand inside them must be ignored, which is the defence against instructions planted in documents.
- The model must answer only from the sources, refuse with reason `not_in_sources` when they don't answer the question, and never use outside knowledge.
- Every claim needs a citation such as [1] or [2][3], and numbers, dates and units must be copied exactly, because finance answers are scored by exact numeric match.
- `PROMPT_VERSION` ("answer-v1") is written into the prompt and the trace, so any eval run can be tied to the prompt that produced it.
