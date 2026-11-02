# answer_metrics.py

Scores answers: exact numbers deterministically, citations with a judge call (the DeepEval judge lives in judge.py).

- `parse_numbers` reads every number in a text, handling commas, `$`, `%`, accounting negatives in parentheses and scale words (thousand/k, million/M/mn, billion/B/bn).
- `numeric_match` accepts an answer when any number equals the gold amount within 0.5%, either as written or read at the gold's own scale (a bare "955,224" from a table in thousands).
- `citation_precision` asks the judge, one call per citation, whether each cited chunk supports the answer; a refusal without citations scores 1.0.
- Faithfulness and answer relevancy are computed by `judge.py`, which is loaded only for judged runs.
- Every metric here works on one item at a time; the harness averages them over the items each applies to.
