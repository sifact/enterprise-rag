# output_check.py

Checks an answer's citations before it is shown.

- Keeps only citation numbers that point at a source the model was actually given (1 to the number of sources).
- Removes markers like "[7]" from the answer text when source 7 doesn't exist, so the employee never sees a dead citation.
- An answer left with no valid citation becomes a refusal with reason `no_support` and empty text: an uncited claim is treated as unsupported.
- Refusals from the model pass through unchanged, keeping its own reason (for example `not_in_sources`).
- Whether each cited source really supports its sentence is measured offline by the LLM judge (citation precision), not checked live, to keep answers fast.
