---
name: production-rag
description: Use when designing, building, tuning, auditing or debugging a retrieval-augmented generation (RAG) system - choosing chunking, embeddings, vector/keyword search, fusion, reranking, access control, guardrails or RAG evaluation, or when answers are wrong, irrelevant, hallucinated or missing citations.
---

# Production RAG

## Overview
A production RAG system is a **measured** retrieval pipeline. Every component (chunker, embedder, hybrid search, reranker, prompt) is a hypothesis that has to beat the previous baseline on a golden set before it stays in.

**Iron rule:** no pipeline change without a before/after number from the eval harness. "It should help" is not evidence.

## Build order (each step is measured against the previous one)
1. **Golden set + eval harness first.** Build 30-50 questions to start, each with the expected answer, gold source chunk/doc IDs and the role allowed to see it. Include out-of-scope and cross-role questions. See `references/evaluation.md`.
2. **Baseline:** structure-aware chunks (~512 tokens) + one dense embedder + top-k. Record retrieval and answer metrics.
3. **Hybrid:** add BM25/sparse retrieval, fuse with RRF, measure again.
4. **Rerank:** cross-encoder over the top 50-100 candidates, keep the top 5-10, measure again.
5. **Chunking ablations:** size, overlap, parent/child, contextual headers. Measure each one.
6. **Query-side tricks** (rewrite, multi-query, HyDE) only if the failure analysis shows query mismatch.
7. **Guardrails + CI:** see `references/security-and-production.md`.

Change one variable at a time. Keep every run in an ablation table (config → recall@k, MRR, nDCG@10, faithfulness, p95 latency, cost/query).

## Quick reference
| Concern | Default | Details |
|---|---|---|
| Chunking | Structure-aware (headings/tables via Docling), ~512 tok, 10-15% overlap, rich metadata | `references/chunking.md` |
| Retrieval | Dense + BM25 hybrid, RRF (k=60) | `references/retrieval.md` |
| Rerank | Cross-encoder on top 50-100 → keep 5-10 | `references/retrieval.md` |
| Access control | **Pre-filter** by role metadata inside the vector DB query, never post-filter | `references/security-and-production.md` |
| Eval | Retrieval and generation scored separately; LLM judge checked against human labels | `references/evaluation.md` |
| Qdrant specifics | **REQUIRED SUB-SKILLS:** `qdrant-search-quality`, `qdrant-multitenancy` | plugin |
| Eval tooling | **REQUIRED SUB-SKILL:** `deepeval` for metrics, datasets and CI | plugin |

## Audit checklist (for an existing pipeline)
- No golden set or eval harness, so regressions can't be detected
- Dense-only retrieval, so exact terms, IDs and codes get missed
- No reranker, or a reranker given too few candidates (<20)
- Chunks >1024 tokens or split mid-table/mid-sentence; no section/page metadata
- Access filter applied after retrieval (leaks via top-k starvation and logs)
- Retrieved text pasted into the prompt as trusted instructions (indirect prompt injection)
- No citations, or citations never checked against the cited chunk
- No "I don't know" path for out-of-scope or no-evidence questions
- Embedding model changed without re-indexing or re-evaluating

## Common mistakes
| Mistake | Fix |
|---|---|
| Tuning on the questions you also report on | Split the golden set into dev/test, and report test only |
| Trusting an LLM judge blindly | Hand-label ~30 items and report judge-human agreement |
| Picking a model from the MTEB average | Use retrieval NDCG@10 on *your* corpus; the leaderboard is only a shortlist |
| Adding every technique at once | One change per run, recorded in the ablation table |
| Quoting blog numbers ("+49% recall") | Only quote numbers you measured |
