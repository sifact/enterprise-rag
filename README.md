# Enterprise RAG with RBAC, Guardrails, Evals and CI

An internal company chatbot over handbook pages, SEC filings and spreadsheets. Each user only retrieves documents their role is allowed to see, and the eval suite proves it.

## Data

There's no private company dataset, so the "company" is **GitLab**, which publishes its internal handbook and files public financial reports. The full corpus definition, with pinned versions, is in [configs/data_sources.yaml](configs/data_sources.yaml).

| Source | What | Role(s) that can see it |
|---|---|---|
| GitLab Handbook | 270 pages sampled from six department folders plus company-wide pages, pinned to commit `322e725a` (2026-10-22) | the matching department; company-wide pages go to every role |
| SEC EDGAR | 10-K for fiscal 2026 (period ending 2026-01-31) and 10-Q for Q2 fiscal 2027 (period ending 2026-07-31) | finance |
| Synthetic XLSX | `budget_fy2027`, `headcount_fy2027`, `vendor_spend_fy2027`; fictional numbers generated with a fixed seed | finance |
| Everything above | | c_level |

Handbook folder → role mapping:

| Role | Handbook folders | Pages |
|---|---|---|
| engineering | `engineering/` | 50 |
| hr | `people-group/`, `total-rewards/`, `hiring/`, `people-policies/` | 45 |
| marketing | `marketing/` | 40 |
| legal | `legal/` | 35 |
| sales | `sales/` | 40 |
| finance | `finance/` | 30 |
| all roles | `company/`, `values/`, `communication/` | 30 |

All of this content is public. The role boundaries are the ones the demo enforces, not real confidentiality, and the RBAC tests check that the boundaries hold.

### Building the corpus

```bash
uv sync
uv run playwright install chromium          # renders the SEC filings to PDF
export SEC_USER_AGENT="Your Name you@example.com"   # required by EDGAR's fair-access policy
uv run enterprise-rag fetch-data            # or --only handbook|sec|synthetic
```

This writes the files to `data/raw/` (git-ignored) and writes `data/raw/manifest.jsonl`, with one row per document and its `allowed_roles`. Re-running with the same config gives the same handbook sample and the same spreadsheets.

### Evaluation data

- **Golden set (ours):** hand-written Q&A pairs with gold source passages and the asking role. It covers in-role questions, cross-role questions (which should be refused), out-of-scope questions and injection attempts. It's split into dev and test sets.
- **FinanceBench (optional):** the 150-question open sample. It covers 32 other companies and no GitLab, so it runs against its own collection and is reported separately.

## Evaluation

The golden set is frozen at [eval/golden/v1.jsonl](eval/golden/v1.jsonl): 84 questions, 41 for tuning (`dev`) and 43 for reporting (`test`).

| Category | Count | How it was made |
|---|---|---|
| Single fact, own department | 24 | LLM-drafted from sampled pages, then reviewed and edited by hand |
| Company-wide page | 6 | LLM-drafted, reviewed |
| Multi-hop / paraphrase | 6 | 2 drafted and reviewed, 4 written by hand |
| SEC filing lookup | 8 | LLM-drafted, each number checked against the filing |
| Spreadsheet lookup | 6 | Computed from the workbooks with pandas |
| Cross-source finance | 4 | 2 computed, 2 hand-written (10-K vs 10-Q) |
| `c_level` asks another department's question | 4 | Derived from answerable items |
| Cross-role (must be refused) | 12 | Answerable questions re-asked by a role that can't see the source |
| Out of scope | 6 | Hand-written |
| Direct prompt injection | 5 | Hand-written |
| Indirect injection (planted in a page) | 3 | Hand-written, with poisoned pages in [eval/fixtures/](eval/fixtures/) |

Gold labels are verbatim quotes, not chunk IDs, so any chunking setup is scored against the same file. How each draft was reviewed is recorded in [eval/golden/review/v1_review.md](eval/golden/review/v1_review.md).

```bash
uv run enterprise-rag eval --pipeline reference-bm25 --split test --retrieval-only
uv run enterprise-rag eval --pipeline reference-bm25 --split test --safety-only
uv run enterprise-rag report eval/runs/*.json
```

**Reference retriever smoke test, not a pipeline result.** The BM25 reference retriever searches whole pages with the role filter applied first. It only exists to check the harness end to end: it never writes answers, so every answer is a refusal.

| Run | hit@5 | MRR@10 | nDCG@10 | Evidence recall@10 | Leak rate |
|---|---|---|---|---|---|
| BM25 over whole pages, test split | 0.828 | 0.810 | 0.823 | 0.862 | 0.000 |

On the safety items it blocked all 5 direct injections and leaked nothing. Its refusal accuracy is 0.857 only because it also "refuses" the 2 indirect-injection test questions, which should be answered.

## Attribution and licenses

- **GitLab Handbook** content © GitLab Inc., licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Source: <https://gitlab.com/gitlab-com/content-sites/handbook> (commit `322e725aa43e37884fdc7aeb27f1e822a696a656`). We sample and chunk pages but don't edit their text. Any redistributed handbook text, including processed chunks, stays under CC BY-SA 4.0. This project isn't affiliated with or endorsed by GitLab Inc.
- **SEC filings** are GitLab Inc.'s public filings, taken from [SEC EDGAR](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001653482) (CIK 0001653482). The filings aren't stored in this repo; the ingestion step downloads them.
- **Synthetic spreadsheets** are fictional numbers generated by this project. They aren't GitLab data.
- **FinanceBench** (if enabled) is © Patronus AI, licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). It's used only for non-commercial evaluation.
