# embedders.py

Wraps the three local models search depends on behind one small interface.

- `FastEmbedders` loads `BAAI/bge-small-en-v1.5` (dense, 384 dimensions), `Qdrant/bm25` (sparse keyword weights) and the `Xenova/ms-marco-MiniLM-L-6-v2` cross-encoder through fastembed, which runs ONNX models on CPU.
- Model files are cached under `models_cache_dir` (`data/cache/models`) so they download once and can be baked into the Docker image.
- Documents and queries are embedded differently where the model expects it: `dense_query` and `sparse_query` use the models' query mode.
- `rerank(query, texts)` returns one relevance score per passage; higher means more relevant, and the scale is the cross-encoder's raw logit.
- Everything else depends only on the `Embedders` protocol, so tests use a deterministic hash-based fake with no downloads.
