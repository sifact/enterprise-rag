"""Read committed evaluation runs (test split only) for the About page."""

from __future__ import annotations

import json
from pathlib import Path

RETRIEVAL_ORDER = ("reference-bm25", "dense", "bm25-chunks", "hybrid", "hybrid-dbsf",
                   "hybrid-rerank")
RETRIEVAL_KEYS = ("hit@5", "hit@10", "mrr@10", "ndcg@10", "evidence_recall@10", "latency_p95_ms")


def _latest_test_runs(runs_dir: Path) -> dict[tuple[str, str], dict]:
    latest: dict[tuple[str, str], dict] = {}
    for path in sorted(runs_dir.glob("*.json")) if runs_dir.exists() else []:
        run = json.loads(path.read_text())
        if run.get("split") != "test":
            continue
        key = (run["pipeline_name"], run["mode"])
        if key not in latest or run["started_at"] >= latest[key]["started_at"]:
            latest[key] = run
    return latest


def load_results(runs_dir: Path) -> dict:
    runs = _latest_test_runs(runs_dir)
    retrieval = [
        {"pipeline": name, **{k: runs[(name, "retrieval")]["aggregates"].get(k) for k in
                              RETRIEVAL_KEYS}}
        for name in RETRIEVAL_ORDER if (name, "retrieval") in runs
    ]
    full, safety = runs.get(("rag", "full")), runs.get(("rag", "safety"))
    return {
        "split": "test",
        "retrieval": retrieval,
        "answers": full["aggregates"] if full else None,
        "safety": safety["aggregates"] if safety else None,
        "run_dates": sorted({r["started_at"][:10] for r in runs.values()}),
    }
