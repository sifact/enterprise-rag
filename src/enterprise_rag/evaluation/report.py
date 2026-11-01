"""Turn run files into the README ablation table."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from enterprise_rag.evaluation.harness import load_run

# Column header -> (aggregate key, format).
COLUMNS = {
    "hit@5": ("hit@5", "{:.3f}"),
    "MRR@10": ("mrr@10", "{:.3f}"),
    "nDCG@10": ("ndcg@10", "{:.3f}"),
    "Faithfulness": ("faithfulness", "{:.3f}"),
    "Leak rate": ("leak_rate", "{:.3f}"),
    "p95 ms": ("latency_p95_ms", "{:.0f}"),
    "$/q": ("cost_per_query_usd", "{:.5f}"),
}
MISSING = "—"


def render_ablation_table(run_paths: Sequence[Path]) -> str:
    header = ["Run", "Config", *COLUMNS]
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for path in run_paths:
        run = load_run(path)
        cells = [path.stem, f"{run.pipeline_name} ({run.mode}, {run.split})"]
        for key, fmt in COLUMNS.values():
            value = run.aggregates.get(key)
            cells.append(MISSING if value is None else fmt.format(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)
