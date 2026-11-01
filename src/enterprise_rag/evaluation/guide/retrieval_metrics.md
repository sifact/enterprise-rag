# retrieval_metrics.py

Rank metrics for one retrieved list, with relevance decided by gold quotes, not chunk IDs.

- `relevance_vector` labels each retrieved chunk relevant or not using `chunk_is_relevant` (right document and ≥ 80% of a gold quote).
- `hit_at_k` and `mrr_at_k` give 1 if a relevant chunk is in the top k, and 1/rank of the first relevant chunk.
- `ndcg_at_k` uses binary gains with a log2 discount; the ideal ordering is the same relevant chunks moved to the top.
- `evidence_recall_at_k` is the share of gold quotes that appear in at least one top-k chunk, so multi-hop items need every passage.
- `doc_hit_at_k` only checks that a gold document appears, as a sanity check next to the quote-based numbers.
