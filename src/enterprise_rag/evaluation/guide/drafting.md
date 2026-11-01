# drafting.py

Samples corpus passages and has an LLM draft one answerable golden item per passage.

- `DraftPlan` sets the accepted-item quotas: 4 single-fact items per department, 6 company-wide, 6 multi-hop and 4 each from the 10-K and 10-Q; `sample_passages` draws 1.5× that many with the config seed.
- Handbook passages are heading-delimited sections with at least 80 prose words, trimmed to whole paragraphs (≤ 450 words) so they stay exact substrings of the page; multi-hop pairs come from two pages in the same folder; SEC passages are whole PDF pages that contain a "Total" table row.
- `draft_item` sends a versioned prompt (`PROMPT_VERSION`) asking for a paraphrased question, an answer, one verbatim quote per passage and, for financial figures, the number with its unit and scale.
- Automatic checks drop a draft (and log why) when the LLM call fails, a quote isn't in its passage, a quote is outside 10-60 words, the question shares over half its word 4-grams with a quote, a number isn't in its quote, or the question repeats an earlier one.
- `draft_all` drafts passages in order until each bucket's quota is met, and `write_review_file` writes the markdown review sheet with accept / edit / drop boxes per item.
