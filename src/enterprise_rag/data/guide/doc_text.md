# doc_text.py

Turns each source document into the page texts that gold quotes are checked against.

- Markdown pages become one `DocPage` with the front matter removed.
- PDFs (the SEC filings) become one `DocPage` per page, numbered from 1, using pypdf's text extraction.
- Spreadsheets become one `DocPage` per sheet: a `Sheet: <name>` line followed by the sheet as CSV. `sheet_to_text` is shared with the computed finance items so their quotes match exactly.
- Parsed files are cached per path, since the 10-K takes seconds to parse and is read for many items.
- `load_fixture_pages` and `load_fixture_roles` read the poisoned injection pages in `eval/fixtures/`, keyed `fixture:<stem>`, with their `allowed_roles` from front matter.
