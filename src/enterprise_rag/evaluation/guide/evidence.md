# evidence.py

Decides whether a retrieved chunk contains a gold quote, whatever the chunking.

- `normalize_text` applies NFKC, maps smart quotes and dashes, joins words hyphenated across a PDF line break, keeps link text but drops URLs, strips HTML and markdown symbols, collapses whitespace and lowercases.
- `quote_match_score` returns the larger of a fuzzy partial match (rapidfuzz `partial_ratio`) and the share of the quote's word 5-grams found in the text.
- When the chunk is shorter than the quote (the chunk boundary cut it), only the 5-gram share is used, so a tiny fragment can't score as a full hit.
- `chunk_is_relevant` is true only when the chunk's document is a gold document and one of that document's quotes scores at or above the threshold (0.80 from config).
- `validate_golden` uses the same scorer at 0.95 to check each stored quote still exists in its document.
