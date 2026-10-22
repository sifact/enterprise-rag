# Retrieval, Fusion and Reranking

## Pipeline
```
query → (optional rewrite) → [dense top-N] + [sparse/BM25 top-N]   (both with role pre-filter)
      → RRF fusion → cross-encoder rerank top 50-100 → keep top 5-10 → context assembly
```

## Hybrid search
- Dense search catches paraphrases. Sparse search (BM25, SPLADE, or BGE-M3 sparse) catches exact terms, product codes, IDs and acronyms. Use both.
- Qdrant supports both natively: named dense + sparse vectors and the Query API with `prefetch` + `fusion: rrf`. See the `qdrant-search-quality` skill.

## Fusion
- **RRF:** `score(d) = Σ 1 / (k + rank_i(d))` with `k = 60`. It's robust and needs no score normalization, so use it as the default.
- Weighted score fusion needs normalized scores and tuning. Try it only if RRF plateaus.
- Deduplicate by `chunk_id` before reranking.

## Reranking
- Run a cross-encoder over (query, chunk) pairs. Give it 50-100 candidates; fewer than 20 leaves little to reorder.
- Candidates to evaluate (Oct 2026; **verify licenses and retrieval scores before choosing**):
  - Open weights: `BAAI/bge-reranker-v2-m3` (Apache-2.0, multilingual), Qwen3-Reranker family, mxbai rerank. Jina reranker weights are CC-BY-NC, so commercial use requires its API.
  - Hosted: Cohere Rerank (v3.5/4), Voyage rerank-2.5.
- Check the latency budget: the reranker is usually the slowest retrieval step. Measure p95.

## Embedding models (shortlist only; pick by NDCG@10 on your own golden set)
- Hosted: Voyage (voyage-3.5 / voyage-4 family), Gemini Embedding, OpenAI text-embedding-3-large.
- Open weights: BGE-M3 (MIT, dense + sparse + multi-vector in one model), Qwen3-Embedding (0.6B/4B/8B), nomic-embed for CPU/local.
- Matryoshka-trained models can be truncated (e.g. 3072 → 1024 dims) to save memory. Measure the quality loss; don't use PCA.
- Changing the model means re-embedding everything into a new collection and re-running the eval.

## Query-side techniques (use only when failure analysis shows query mismatch)
| Technique | Helps when |
|---|---|
| Query rewrite | Conversational follow-ups ("what about last year?") need history folded in |
| Multi-query + RRF | Vague questions that could be phrased many ways |
| HyDE | Short queries against long technical docs |
| Decomposition | Multi-part or comparison questions |
Each one adds an LLM call, so report the gain against the added latency and cost.

## Context assembly
- Order chunks by rerank score, cap them with a token budget, and label each with `[doc_id:chunk_id] title > section (p. N)` so citations can be checked.
- Wrap retrieved text in delimiters and tell the model it is **data, not instructions** (see security-and-production.md).
- If the top rerank score is below a threshold you calibrated on the dev set, answer "I don't have enough information" instead of guessing.
