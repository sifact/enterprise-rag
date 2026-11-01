# harness.py

Runs a pipeline over golden items, scores each item and writes a run file.

- For every item it calls `retrieve` with the role the harness supplies, checks for role leaks, and on answerable items (except indirect injection, whose pages aren't indexed then) computes hit@5/10, MRR@10, nDCG@10, evidence recall@10 and document hit@10.
- Unless `--retrieval-only`, it calls `answer` and adds refusal correctness, false refusals, numeric match, answer leaks against the cross-role item's twin, and injection blocking (refusal for direct attacks, no canary for planted ones).
- With a judge it adds DeepEval faithfulness and answer relevancy plus citation precision; a failed judge call is recorded on the item instead of stopping the run.
- `aggregate` averages each metric over the items it applies to and adds leak rate, p50/p95 latency and cost per query when prices are configured.
- `write_run` saves `eval/runs/<date>-<pipeline>-<split>[-mode].json` with IDs, scores and metrics only: no chunk text, no API key.
