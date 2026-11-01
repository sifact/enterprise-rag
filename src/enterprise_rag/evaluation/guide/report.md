# report.py

Builds the README ablation table from run files.

- `render_ablation_table` reads each run file with `load_run`, one table row per file.
- Columns are Run, Config, hit@5, MRR@10, nDCG@10, Faithfulness, Leak rate, p95 ms and $/q.
- The Config cell shows the pipeline name, the run mode (full, retrieval or safety) and the split.
- A metric the run didn't compute (e.g. faithfulness in a retrieval-only run) shows as "—" instead of 0, so a missing number is never mistaken for a bad one.
- Only `test`-split runs should go in the README; dev runs are for tuning.
