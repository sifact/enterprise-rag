# chunking.py

Cuts each document into passages for search, keeping its structure and its access labels.

- Every chunk copies its document's `allowed_roles`, department, title and source URL, so the index can filter by role before ranking anything.
- Handbook pages split on headings first; small neighbouring sections (under `min_chunk_words`) share a chunk, each section's heading stays as the first line, and the chunk is named after the section path (e.g. "Policy > Exceptions").
- Long sections are packed sentence by sentence up to `chunk_words` (300) with about 40 words of overlap, so no passage ends mid-sentence; lists and table rows count as whole lines.
- PDF filings are packed page by page and keep the page number; spreadsheet sheets become groups of 20 rows that repeat the header row and overlap by 2 rows, so a quoted row group stays whole.
- `strip_hidden_text` removes HTML comments, markdown comment lines and `display:none` blocks before chunking, because text a reader never sees must not reach the model.
