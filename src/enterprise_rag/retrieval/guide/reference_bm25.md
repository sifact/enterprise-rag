# reference_bm25.py

A minimal BM25 retriever with a role pre-filter, used to check the evaluation harness end to end.

- Each document page is one "chunk": a whole handbook page, one PDF page of a filing, or one spreadsheet sheet, read with the same `load_doc_pages` the gold quotes use.
- At construction it builds a separate `BM25Okapi` index per role over only the chunks that role may see, so filtering happens before scoring, never after.
- Poisoned fixture pages are added only when `fixtures_dir` is given (safety runs), with roles from their front matter.
- `retrieve` tokenizes lowercase words and returns the top-k chunks of the caller's role index with their BM25 scores.
- `answer` always refuses because there is no generator; its numbers are a harness smoke test, not a pipeline result.
