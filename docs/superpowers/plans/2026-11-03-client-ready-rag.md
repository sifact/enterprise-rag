# Client-Ready RAG: Pipeline, API and Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the CLI-only state with a working role-aware RAG system (chunking, hybrid search, reranking, guardrails, cited answers), measure it on golden set v1, and ship it as one web app with Playground and About tabs that a potential customer can use.

**Architecture:** Documents from the manifest are chunked with their `allowed_roles` copied onto every chunk and indexed in embedded Qdrant (dense + BM25 sparse vectors). A query runs an input guard, then hybrid search with the role filter inside every prefetch, RRF fusion, a cross-encoder rerank, an evidence threshold, a context guard that drops passages carrying instructions, cited generation on Groq and a citation check. FastAPI exposes it with a signed demo session that carries the role; a React app is served by the same process.

**Tech Stack:** Python 3.13, uv, qdrant-client (embedded, on-disk), fastembed 0.9 (`BAAI/bge-small-en-v1.5`, `Qdrant/bm25`, `Xenova/ms-marco-MiniLM-L-6-v2`), Groq (`qwen/qwen3.8-27b` answers, `meta-llama/llama-prompt-guard-2-86m` guard, `openai/gpt-oss-120b` judge), FastAPI + uvicorn, React 19 + Vite + TypeScript + Tailwind CSS v4, Playwright for screenshots, Docker.

**Spec:** No separate design doc: the user skipped design questions. Requirements are the user's request ("complete this project, no CLI; modern dark/light UI, dark default; tabs Playground and About; About explains everything for a potential customer"), the "Client-ready projects" section of `~/.claude/CLAUDE.md`, the build order and rules in `.claude/skills/production-rag/`, and the golden-set spec `docs/superpowers/specs/2026-10-23-golden-set-eval-design.md` (metrics, pipeline interface).

## Global Constraints

- RBAC: the role filter `allowed_roles` contains `<role>` goes **inside every Qdrant prefetch** (dense and sparse); never post-filter. An unknown role returns no results.
- In the API the role comes only from a server-signed session cookie set by `POST /api/session`; a `role` field in the ask request body is ignored.
- Model names, thresholds, chunk sizes and limits live in `configs/rag.yaml`, never in code.
- `GROQ_API_KEY` stays server-side; the browser never sees it. Run files and API responses never contain it.
- Public limits: question length 1-500 characters; 6 asks per minute and 100 per day per client IP; answers cached per (role, normalized question, options).
- Every number shown in the UI comes from a committed run file in `eval/runs/`; the About page labels the data as public (GitLab handbook, SEC filings) or fictional (spreadsheets).
- Retrieval choices are kept only if they beat the previous step on the **dev** split; README and UI report **test** split numbers.
- Layout per `~/.claude/CLAUDE.md`: new stage packages `indexing/`, `retrieval/`, `guardrails/`, `generation/`, `pipeline/`, `serving/` under `src/enterprise_rag/`; each core ML module gets `guide/<module>.md` (5 bullets); public API from each `__init__.py`.
- UI: tabs Playground and About at the top; light and dark themes, dark by default, choice stored in `localStorage` and applied before first paint; works at 360 px width; visible keyboard focus; respects reduced motion. Design follows the `frontend-design` skill.
- Commit messages never mention Claude or AI.

## Review Focus

1. **A visitor tampers with the role** (edits the cookie, or sends `"role": "c_level"` in the ask body) → 401 for a bad cookie, body role ignored. Test: `test_tampered_session_rejected`, `test_body_role_ignored` (Task 7).
2. **A retrieved passage carries planted instructions** → the passage is dropped before generation and listed as removed. Test: `test_context_guard_drops_flagged_chunk` (Task 5).
3. **Empty, whitespace-only or 501-character questions** → 422 with a readable message, not a 500. Test: `test_question_length_validated` (Task 7).
4. **Groq unavailable or rate-limited past retries** → API answers 503 with a plain message and the UI shows an error state; nothing crashes. Test: `test_llm_outage_returns_503` (Task 7).
5. **The model cites a source number that wasn't given** (e.g. `[7]` with 5 sources) → the citation is dropped; an answer left with no valid citation becomes a refusal. Test: `test_invalid_citations_dropped_and_uncited_answer_refused` (Task 5).

---

### Task 1: Structure-aware chunking with role labels

**Files:**
- Create: `configs/rag.yaml`, `src/enterprise_rag/indexing/__init__.py`, `src/enterprise_rag/indexing/chunking.py`, `src/enterprise_rag/indexing/guide/chunking.md`, `tests/indexing/test_chunking.py`
- Modify: `src/enterprise_rag/config.py` (add `RagConfig`, `load_rag_config`)

**Interfaces:**
- Consumes: `DocumentRecord`, `load_doc_pages`, `load_fixture_pages`, `load_fixture_roles` (`enterprise_rag.data`).
- Produces: `RagConfig` (frozen) with `chunk_words: int` (300), `chunk_overlap_words: int` (40), `sheet_rows_per_chunk: int` (20), `index_dir: Path` (`data/index`), `collection: str` (`chunks_v1`), `embed_model`, `sparse_model`, `rerank_model`, `models_cache_dir: Path` (`data/cache/models`), `prefetch_limit: int` (50), `rerank_candidates: int` (40), `context_chunks: int` (6), `evidence_threshold: float` (set in Task 6), `guard_model`, `guard_threshold: float` (0.9), `generator_model`, `max_question_chars: int` (500), `rate_per_minute: int` (6), `rate_per_day: int` (100); `load_rag_config(path=PROJECT_ROOT/"configs/rag.yaml")`.
- Produces: `Chunk` (frozen) with `chunk_id` (`f"{doc_id}#c{index:04d}"`), `doc_id`, `title`, `section: str`, `page: int | None`, `text: str`, `context_header: str` (`"Title > Section"` or `"Title > page N"`), `allowed_roles: tuple[str, ...]`, `department: str`, `source_url: str | None`; `chunk_document(record, pages) -> list[Chunk]`; `chunk_corpus(manifest, raw_dir, fixtures_dir=None) -> list[Chunk]`; `strip_hidden_text(text) -> str`.

- [ ] **Step 1: Write failing tests:**
  - `test_markdown_split_on_headings_with_section_path`: two `##` sections → two chunks whose `section` is the heading text and `context_header` starts with the title.
  - `test_long_section_split_with_overlap_never_mid_sentence`: a 700-word section → ≥ 3 chunks, each ≤ `chunk_words` + one sentence, consecutive chunks share text, and every chunk ends with sentence punctuation.
  - `test_every_chunk_copies_document_roles`: all chunks of a `("c_level","legal")` record carry exactly those roles.
  - `test_pdf_chunks_keep_page_numbers`.
  - `test_sheet_chunks_repeat_header_row`: a 45-row sheet → 3 chunks, each starting with `Sheet: <name>` and the header line.
  - `test_strip_hidden_text`: removes `<!-- -->` comments, `[//]: # (...)` lines and `display:none` elements; keeps visible text.
  - `test_computed_spreadsheet_quotes_still_match_chunks`: for each `computed_items` evidence, some chunk of that doc gets `quote_match_score ≥ 0.8` (keeps golden v1 scoreable).
- [ ] **Step 2: Run** `uv run pytest tests/indexing -v` → FAIL (imports).
- [ ] **Step 3: Implement.** Markdown: split on headings (levels 1-4), then paragraphs, then sentences (regex on `. ! ?` + space + capital), packing to `chunk_words` with `chunk_overlap_words` carried over. PDF: per page, same packing. XLSX: row groups of `sheet_rows_per_chunk` with the header repeated. `strip_hidden_text` runs on page text before chunking (text a reader never sees must not reach the model).
- [ ] **Step 4: Run** `uv run pytest -q` → all pass. Also `uv run python -c` a corpus count: print chunk count and max words (expect ~1,500-3,000 chunks, max ≤ 340 words).
- [ ] **Step 5: Commit** `"Add structure-aware chunking with role labels"`.

### Task 2: Embedded Qdrant index (dense + BM25)

**Files:**
- Create: `src/enterprise_rag/indexing/embedders.py`, `src/enterprise_rag/indexing/store.py`, `guide/embedders.md`, `guide/store.md`, `tests/indexing/test_store.py`
- Modify: `pyproject.toml` (`qdrant-client>=1.15`, `fastembed>=0.9`), `.gitignore` (nothing: `/data/` already covers `data/index` and `data/cache`), `src/enterprise_rag/cli.py` (`build-index`)

**Interfaces:**
- Consumes: `Chunk`, `chunk_corpus` (Task 1), `RagConfig`.
- Produces: `class Embedders(Protocol)`: `dense(texts) -> list[list[float]]`, `dense_query(text) -> list[float]`, `sparse(texts) -> list[SparseVec]`, `sparse_query(text) -> SparseVec`, `rerank(query, texts) -> list[float]`; `SparseVec(indices: list[int], values: list[float])`; `FastEmbedders(cfg)` (models cached in `cfg.models_cache_dir`); `build_index(chunks, embedders, client, collection) -> int`; `open_client(cfg) -> QdrantClient` (on-disk at `cfg.index_dir`); payload fields `chunk_id, doc_id, title, section, page, text, context_header, allowed_roles, department, source_url`; keyword payload index on `allowed_roles`. Dense input is `context_header + "\n" + text`; sparse input the same.
- CLI: `enterprise-rag build-index [--with-fixtures]` writes collection `chunks_v1` (and `chunks_v1_safety` with fixtures).

- [ ] **Step 1: Write failing tests** with a deterministic `FakeEmbedders` (hash-based vectors) and `QdrantClient(":memory:")`: `test_build_index_stores_payload_and_role_index`, `test_rebuild_replaces_collection` (building twice leaves one copy of each chunk).
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** Recreate the collection on each build (named `dense` 384-d cosine vector, `bm25` sparse vector with `Modifier.IDF`); upsert in batches of 128 with UUIDv5 ids from `chunk_id`.
- [ ] **Step 4: Run** tests, then `uv run enterprise-rag build-index` and `--with-fixtures` on the real corpus → prints chunk counts; time it.
- [ ] **Step 5: Commit** `"Add embedded Qdrant index with dense and BM25 vectors"`.

### Task 3: Hybrid retriever with role pre-filter and reranking

**Files:**
- Create: `src/enterprise_rag/retrieval/hybrid.py`, `retrieval/guide/hybrid.md`, `tests/retrieval/test_hybrid.py`
- Modify: `src/enterprise_rag/retrieval/types.py` (add `rerank_score: float | None = None` to `RetrievedChunk`; keep existing fields), `src/enterprise_rag/retrieval/__init__.py`, `src/enterprise_rag/cli.py` (register pipelines `dense`, `bm25-chunks`, `hybrid`, `hybrid-rerank` for `eval --retrieval-only`)

**Interfaces:**
- Consumes: `Embedders`, `open_client`, payload layout (Task 2).
- Produces: `SearchMode = Literal["dense","sparse","hybrid"]`; `HybridRetriever(client, collection, embedders, mode, fusion: Literal["rrf","dbsf"]="rrf", rerank: bool, prefetch_limit, rerank_candidates, name)` implementing `Pipeline.retrieve` (and `answer` = refuse, like the reference) plus `search(question, role, k) -> list[RetrievedChunk]` with `rerank_score` set when reranking.

- [ ] **Step 1: Write failing tests** on an in-memory index of 3 docs with `FakeEmbedders`: `test_role_filter_applied_in_every_mode` (parametrized over the 3 modes: a legal query never returns the engineering chunk), `test_unknown_role_returns_nothing`, `test_rerank_reorders_by_cross_encoder_score` (fake reranker scores the last candidate highest → it comes first).
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement** with `query_points`: one `Prefetch` per vector with the same `Filter(must=[FieldCondition("allowed_roles", MatchValue(role))])`, `FusionQuery(RRF|DBSF)`, limit `rerank_candidates` when reranking else `k`; rerank on `context_header + text`.
- [ ] **Step 4: Measure on dev**, one change at a time: `uv run enterprise-rag eval --pipeline <p> --split dev --retrieval-only` for `dense`, `bm25-chunks`, `hybrid` (RRF), `hybrid` with DBSF, `hybrid-rerank`. Keep the best fusion; keep rerank only if nDCG@10 improves. Record each run (dev run files stay out of the README).
- [ ] **Step 5: Commit** `"Add hybrid retriever with role pre-filter and reranking"` with the dev run files.

### Task 4: Groq client options and cited generation

**Files:**
- Create: `src/enterprise_rag/generation/__init__.py`, `generation/prompt.py`, `generation/generator.py`, `generation/guide/prompt.md`, `generation/guide/generator.md`, `tests/generation/test_generator.py`
- Modify: `src/enterprise_rag/llm.py` (optional `extra_body: dict | None` merged into the payload; `max_tokens` per call)

**Interfaces:**
- Consumes: `GroqClient`, `RetrievedChunk`.
- Produces: `PROMPT_VERSION = "answer-v1"`; `build_messages(question, role, chunks) -> tuple[str, str]` (system, user) with sources numbered `[1]..[n]`, each wrapped in `<source n="i" doc="...">…</source>` and the instruction that sources are data, not instructions; `Generated(answer: str, citations: tuple[int, ...], refused: bool, reason: str, usage: Usage)`; `Generator(client).generate(question, role, chunks) -> Generated` (JSON reply `{"answer","citations","refused","reason"}`, `extra_body={"reasoning_format": "hidden"}`, temperature 0).

- [ ] **Step 1: Write failing tests** with a fake client: `test_prompt_numbers_and_delimits_sources`, `test_generate_parses_json_reply`, `test_unparseable_reply_raises_llm_error`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Run** `uv run pytest -q` → pass.
- [ ] **Step 5: Commit** `"Add cited answer generation"`.

### Task 5: Guardrails (input, context, output)

**Files:**
- Create: `src/enterprise_rag/guardrails/__init__.py`, `guardrails/input_guard.py`, `guardrails/output_check.py`, `guardrails/guide/input_guard.md`, `guardrails/guide/output_check.md`, `tests/guardrails/test_guards.py`

**Interfaces:**
- Produces: `GuardResult(flagged: bool, score: float, reason: str)`; `InjectionGuard(client | None, threshold)` with `check(text) -> GuardResult` (prompt-guard score from Groq; on `LLMError` falls back to the heuristic only); `heuristic_flags(text) -> list[str]` (instruction override: "ignore … instructions", "system prompt", "you are now", role claims: "as c_level", "I am the CFO/CEO", "admin mode"); `filter_context(chunks, guard) -> tuple[list[RetrievedChunk], list[tuple[RetrievedChunk, str]]]` (kept, removed with reason); `check_citations(generated, n_sources) -> Generated` (drops out-of-range citations; a non-refused answer with no valid citation becomes `refused=True, reason="no_support"`).

- [ ] **Step 1: Write failing tests:** `test_heuristic_flags_role_claims_and_overrides` (each of the 5 golden direct-injection questions is flagged; 6 ordinary questions aren't), `test_guard_falls_back_to_heuristic_on_llm_error`, `test_context_guard_drops_flagged_chunk` (Review Focus 2), `test_invalid_citations_dropped_and_uncited_answer_refused` (Review Focus 5).
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Run** → pass.
- [ ] **Step 5: Commit** `"Add input, context and output guardrails"`.

### Task 6: RAG pipeline, evidence threshold and full evaluation

**Files:**
- Create: `src/enterprise_rag/pipeline/__init__.py`, `pipeline/rag.py`, `pipeline/guide/rag.md`, `tests/pipeline/test_rag.py`
- Modify: `src/enterprise_rag/retrieval/types.py` (add `trace: dict | None = None` to `PipelineResponse`), `src/enterprise_rag/cli.py` (register `rag` for `eval`; `eval --safety-only` builds against `chunks_v1_safety`), `configs/rag.yaml` (`evidence_threshold`), `README.md` (results)

**Interfaces:**
- Consumes: Tasks 3-5.
- Produces: `RagPipeline(retriever, guard, generator, cfg, name="rag")` implementing `Pipeline`; `answer()` order: input guard (flagged → refuse `"blocked_input"`) → `search(k=context_chunks)` → top `rerank_score` < `evidence_threshold` or no chunks → refuse `"no_evidence"` → `filter_context` → generate → `check_citations`. `trace` holds `{"stages": {name: ms}, "guard": {...}, "removed": [{chunk_id, doc_id, reason}], "top_score": float, "refusal_reason": str | None, "prompt_version": str, "model": str}`. `citations` are chunk IDs.

- [ ] **Step 1: Write failing tests** with fakes: `test_blocked_input_skips_search`, `test_low_evidence_refuses_without_llm_call`, `test_answer_cites_chunk_ids_and_fills_trace`, `test_role_passed_to_search_unchanged`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Calibrate** `evidence_threshold` on **dev**: print top rerank scores for answer vs out-of-scope/cross-role items and pick the value that keeps false refusals on answer items ≤ 10%; write it to `configs/rag.yaml` with a comment naming the run.
- [ ] **Step 5: Evaluate on test** (background, rate-limited): `eval --pipeline hybrid-rerank --split test --retrieval-only`, `eval --pipeline rag --split test` (answers + judge), `eval --pipeline rag --split test --safety-only`. Gate: `leak_rate == 0`. Update the README results table from `enterprise-rag report` (test runs only) and add the diagrams to the README.
- [ ] **Step 6: Commit** `"Add RAG pipeline with evidence threshold and test-split results"` with the run files.

### Task 7: API with signed demo sessions, limits and caching

**Files:**
- Create: `src/enterprise_rag/serving/__init__.py`, `serving/app.py` (routes), `serving/schemas.py`, `serving/session.py`, `serving/limits.py`, `serving/results.py`, `serving/examples.py`, `tests/serving/test_api.py`
- Modify: `pyproject.toml` (`fastapi`, `uvicorn[standard]`, `httpx` dev), `src/enterprise_rag/cli.py` (`serve [--host] [--port]`)

**Interfaces:**
- Consumes: `RagPipeline` (Task 6), run files, manifest.
- Produces routes: `GET /api/health`; `GET /api/meta` → roles (name, plain description, document counts), example questions grouped `own_team | other_team | attacks`, corpus stats; `POST /api/session {role}` → sets HMAC-signed `session` cookie (secret from `SESSION_SECRET`, random per process if unset); `POST /api/ask {question, options: {rerank: bool}}` → `AskResponse {answer, refused, refusal_reason, citations: [{n, chunk_id, doc_id, title, page, source_url, snippet}], retrieved: [{chunk_id, doc_id, title, section, page, score, rerank_score, allowed_roles, cited}], removed, guard, timings, model, cached}`; `GET /api/results` → test-split aggregates for the ablation table and safety numbers; static files from `web/dist` at `/` with SPA fallback. `create_app(pipeline_factory, cfg) -> FastAPI` so tests inject fakes.

- [ ] **Step 1: Write failing tests** with `TestClient` and a fake pipeline: `test_ask_requires_session`, `test_tampered_session_rejected` and `test_body_role_ignored` (Review Focus 1), `test_question_length_validated` (Review Focus 3), `test_rate_limit_returns_429_after_6_per_minute`, `test_repeat_question_served_from_cache`, `test_llm_outage_returns_503` (Review Focus 4), `test_results_endpoint_reads_test_runs_only`, `test_responses_never_contain_api_key`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Run** → pass; then `uv run enterprise-rag serve` and `curl` `/api/meta`, a session, and one real ask per role class (own team, other team, attack); read the bodies.
- [ ] **Step 5: Commit** `"Add API with signed demo sessions, limits and caching"`.

### Task 8: Web app shell, themes and Playground

**Files:**
- Create: `web/` (Vite React TS project: `index.html`, `package.json`, `vite.config.ts` with `/api` proxy to `:8000`, `src/main.tsx`, `src/App.tsx`, `src/api.ts`, `src/theme.ts`, `src/components/*`, `src/pages/Playground.tsx`), `web/DESIGN.md` (the design plan from the `frontend-design` skill)
- Modify: `.gitignore` (`web/node_modules/`, `web/dist/`)

**Interfaces:**
- Consumes: the API in Task 7 (types mirrored in `src/api.ts`).
- Produces: hash routes `#/playground` (default) and `#/about`; `ThemeToggle` (dark default, `localStorage["theme"]`, inline script in `index.html` sets the class before paint); Playground: "Signed in as" role switcher (calls `/api/session`), example questions in the three groups, question box with a 500-character counter, ask button, answer with citation chips linking to sources, refusal card that names the reason in plain words, "How it answered" panel (guard check, passages searched with scores and role labels, removed passages, stage timings), "Ask as another role" shortcut that re-asks the same question as a different role.

- [ ] **Step 1: Design plan first** per the `frontend-design` skill: write `web/DESIGN.md` (palette for both themes, type, layout wireframes, principles), review it against the brief, revise generic choices.
- [ ] **Step 2: Build** the shell, themes and Playground; `npm --prefix web run build` passes `tsc` with no errors.
- [ ] **Step 3: Verify in a browser** (Playwright, against `enterprise-rag serve`): screenshots at 1440 px and 390 px, both themes, for: empty state, an answered question, a refusal, an error (API stopped). Look at each and fix layout issues and console errors.
- [ ] **Step 4: Commit** `"Add web app shell, themes and Playground"`.

### Task 9: About page for potential customers

**Files:**
- Create: `web/src/pages/About.tsx`, `web/src/components/HowItWorks.tsx` (inline SVG diagram), `web/src/content/about.ts` (all copy in one place)

**Interfaces:**
- Consumes: `GET /api/results`, `GET /api/meta`.
- Produces: About sections in this order: the problem; what it does for you; try it (link to Playground); how it works (diagram: label → filter → search → check → answer); the data (sources, who sees what, public vs fictional); measured results (test split table and safety numbers from `/api/results`, each with a one-line plain meaning); limitations; running it on your documents; tech stack.

- [ ] **Step 1: Write the copy** in `about.ts` for a non-technical buyer (plain words, short sections, every number from `/api/results` or the manifest).
- [ ] **Step 2: Build** the page and diagram; build passes.
- [ ] **Step 3: Verify** with screenshots in both themes at both widths; check every number against the run files.
- [ ] **Step 4: Commit** `"Add About page for potential customers"`.

### Task 10: Packaging, CI and final verification

**Files:**
- Create: `Dockerfile` (stage 1 Node builds `web/dist`; stage 2 Python with uv: `fetch-data`, `build-index`, model download, needs build arg `SEC_USER_AGENT`; final stage copies the package, `web/dist`, `data/index`, model cache; runs `enterprise-rag serve --host 0.0.0.0 --port $PORT`), `.dockerignore`, `Makefile` (`make run`: build web + serve), `.github/workflows/ci.yml` (ruff, pytest, `npm run build`, `enterprise-rag gate eval/runs/*-rag-test-safety.json` fails when `leak_rate > 0`)
- Modify: `src/enterprise_rag/cli.py` (`gate`), `README.md` (Run the demo, screenshots, diagrams)

- [ ] **Step 1: Write failing test** `test_gate_fails_on_leak` (a run file with `leak_rate` 0.1 → exit code 1; 0.0 → 0). **Step 2-4:** implement, run, pass.
- [ ] **Step 5:** `docker build` and run the image locally; open both tabs; ask one question per example group.
- [ ] **Step 6:** `uv run ruff check src tests && uv run pytest -q && npm --prefix web run build` all clean.
- [ ] **Step 7: Commit** `"Add Docker image, CI and demo instructions"`. Deployment waits for the user's choice of host.

---

## Addendum (2026-11-03): deploy everything on Vercel

**Why:** the user needs a free host without Docker or a card. The local-model backend needs ~550 MB of RAM and a 56 MB on-disk index, which fits neither Vercel functions (250 MB bundle, no persistent disk) nor Render/Koyeb free (512 MB). Hugging Face Spaces and Google Cloud are ruled out by the user.

**Architecture change:** the search index moves to a Qdrant Cloud free cluster, and embeddings are computed by Qdrant Cloud Inference (`sentence-transformers/all-minilm-l6-v2` dense, `qdrant/bm25` sparse; both free on free clusters). The backend becomes a slim FastAPI function on Vercel; the React app is served by Vercel as static files. The cross-encoder relevance check is replaced by the top dense similarity, calibrated on dev.

**Supersedes:** Task 10's Docker step (Docker removed at the user's request).

### Task 11: Slim serving import chain
- Package `__init__` files that pull heavy modules (pandas, fastembed, rapidfuzz, DeepEval, playwright) load them lazily, so `enterprise_rag.serving` + `enterprise_rag.pipeline.rag` import with only fastapi, qdrant-client, requests, pyyaml, python-dotenv and pydantic installed.
- `enterprise-rag export-web-data` writes `deploy/meta.json` (roles, examples, corpus counts) so the function never reads the manifest or golden set.
- Test: `test_serving_imports_stay_light` (a subprocess imports the serving entry point and asserts pandas, fastembed, deepeval and rapidfuzz are not in `sys.modules`).

### Task 12: Qdrant Cloud index and retriever
- `indexing/cloud_store.py`: `build_cloud_index(chunks, client, collection, dense_model, sparse_model)` upserts text as `models.Document` for both vectors, with a keyword payload index on `allowed_roles`.
- `retrieval/cloud.py`: `CloudRetriever(client, collection, mode, fusion, dense_model, sparse_model)` implementing `search(question, role, k)` with the role filter inside every prefetch, plus `evidence(question, role)` = top dense cosine.
- Tests with a fake client that records requests: role filter in every prefetch; `Document` objects carry the configured model names.
- Measure on dev (dense, sparse, hybrid RRF, hybrid DBSF), keep the best; calibrate `evidence_threshold` (≤ 1 in 20 false refusals); run test-split safety and no-judge full evaluations; update README and the About copy (MiniLM replaces bge-small; no cross-encoder).

### Task 13: Vercel deployment
- `api/index.py` exposes the FastAPI app; `vercel.json` builds `web/` to static files, routes `/api/*` to the function (maxDuration 60 s), and `requirements.txt` lists only the slim runtime dependencies.
- Session secret, Groq key and Qdrant credentials come from Vercel environment variables; the in-memory cache and rate limits are per function instance (documented).
- Deploy, run the browser checks against the live URL (both tabs, both themes, desktop and phone), then add the live URL to the README and `~/Documents/deployed-links.md`.
