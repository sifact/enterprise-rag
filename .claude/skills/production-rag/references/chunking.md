# Chunking

## Parse before you chunk
- Use **Docling** (or similar) to turn PDF/DOCX/XLSX into structured elements: headings, paragraphs, tables, lists, page numbers. Chunking raw extracted text loses the structure that matters most.
- Tables: keep each table whole as one chunk (render it to markdown) together with its caption and section heading. If it's too large, split by row groups and repeat the header row in every piece.
- Spreadsheets: one chunk per logical table or sheet region, with column headers included in every chunk.

## Strategies (try them in this order, measuring each)
| Strategy | When | Notes |
|---|---|---|
| Structure-aware recursive (headings → paragraphs → sentences) | Default for enterprise docs | ~512 tokens, 10-15% overlap; never split mid-sentence or mid-table |
| Parent/child (small-to-big) | Precise matching but answers need surrounding context | Embed ~128-256 token children; return the ~1-2k token parent section to the LLM |
| Contextual chunk headers | Chunks that are ambiguous on their own ("it increased 5%") | Prepend `Doc title > Section > Subsection` to the text before embedding |
| Contextual retrieval (Anthropic) | Header prefixes aren't enough | An LLM writes a 1-2 sentence context per chunk, which is prepended before embedding **and** BM25 indexing; use prompt caching to keep ingestion cost down |
| Semantic chunking (embedding breakpoints) | Long unstructured prose | Often no better than recursive splitting in published comparisons; only keep it if your eval shows a gain |
| Fixed-size | Logs, code-like, uniform text | Simple baseline |

## Metadata on every chunk (needed for filtering, citations and debugging)
`doc_id, chunk_id, source_path, title, section_path, page, chunk_index, allowed_roles[], department, doc_date/version, content_hash`

## Ablations worth running
- Chunk size 256 / 512 / 1024
- Overlap 0 / 10% / 20%
- With vs without contextual headers
- Flat vs parent/child

Report recall@k and nDCG@10 for each.

## Pitfalls
- Re-chunking without re-embedding, or a mix of old and new chunks left in one collection. Version the collection name.
- Dedupe near-identical boilerplate (footers, disclaimers) or it floods top-k.
- Tokens ≠ characters. Size chunks with the embedder's tokenizer.
