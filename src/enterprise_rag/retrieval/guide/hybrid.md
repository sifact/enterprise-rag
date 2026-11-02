# hybrid.py

Searches only the passages a role may read, then reorders them with a reranker.

- Every query carries a Qdrant filter "`allowed_roles` contains the asking role"; in hybrid mode the same filter sits inside both prefetches, so other roles' passages are never scored, fused or reranked.
- `mode="dense"` searches meaning (bge-small vectors), `mode="sparse"` searches keywords (BM25 with IDF), and `mode="hybrid"` runs both and fuses the two ranked lists with RRF or DBSF.
- With `rerank=True` it fetches `rerank_candidates` (40) passages, scores each (question, passage) pair with the cross-encoder, sorts by that score and keeps the top k.
- Each result keeps display details in `meta` (title, section, page, allowed roles, source URL) for citations and the UI.
- `answer()` always refuses: these retrievers are used for the retrieval ablation; the answer pipeline adds generation on top.
