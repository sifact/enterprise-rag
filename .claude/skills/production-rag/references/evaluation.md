# RAG Evaluation

## Golden set
- Start with 30-50 items and grow to 100+. Fields: `id, question, reference_answer, gold_chunk_ids[] (or gold_doc_ids[]), role, category`.
- Categories to cover:
  - Single-fact
  - Multi-hop / multi-chunk
  - Table/number lookup
  - Keyword/ID lookup
  - Paraphrase
  - **Out-of-scope** (expected: refusal)
  - **Cross-role** (a finance question asked by an engineering user; expected: no leak, refusal)
  - **Adversarial** (injection, PII extraction)
- Source questions from real docs. LLM-generated questions are fine to start, but have a human review them and drop the trivial ones that copy chunk wording verbatim.
- Split into **dev** (for tuning) and **test** (only for reporting). Never tune on test.
- Version the set in git (`eval/golden/v1.jsonl`). When the corpus changes, re-check the gold IDs.

## Metrics: score retrieval and generation separately
| Layer | Metric | Meaning |
|---|---|---|
| Retrieval | Hit rate / recall@k | Was any or all of the gold evidence in the top-k? |
| Retrieval | MRR | How high was the first relevant chunk? |
| Retrieval | nDCG@10 | Ranking quality with graded relevance |
| Generation | Faithfulness / groundedness | Is every claim supported by the retrieved context? |
| Generation | Answer relevance / correctness | Does it answer the question, matching the reference? |
| Generation | Citation precision | Does each cited chunk actually support the sentence that cites it? |
| Safety | Leak rate, refusal accuracy, injection block rate | From the cross-role, out-of-scope and adversarial items |
| Ops | p50/p95 latency, tokens and $ per query | From tracing |

Retrieval metrics are deterministic and cheap: compute them in plain Python against the gold IDs. Use the `deepeval` skill (faithfulness, answer relevancy, contextual precision/recall) or RAGAS for the LLM-judged metrics.

## LLM-as-judge hygiene
- Hand-label ~30 items and report the judge's agreement with humans. If agreement is low, fix the rubric before trusting any numbers.
- Use a different (or stronger) model as judge than the generator, with temperature 0 and a fixed judge prompt version.
- Generation is non-deterministic. For headline numbers, run 3 times and report the mean ± spread.

## Ablation table (put it in the README)
| Run | Config change | recall@5 | MRR | nDCG@10 | Faithfulness | p95 ms | $/q |
|---|---|---|---|---|---|---|---|
| 0 | baseline dense, 512 tok | | | | | | |
| 1 | + BM25 hybrid (RRF) | | | | | | |
| 2 | + rerank | | | | | | |

## CI
- A fast subset (~20 items + all safety items) runs on every push, with thresholds that fail the build (e.g. recall@5 ≥ baseline − 2 pts, leak rate = 0).
- The full set runs nightly or on demand. Store results as JSON artifacts so regressions can be diffed.
- Failure analysis: for each miss, label the cause as retrieval miss, ranking miss, generation error or bad gold label. Fix the biggest group first.
