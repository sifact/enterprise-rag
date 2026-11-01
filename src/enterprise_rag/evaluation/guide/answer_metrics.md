# answer_metrics.py

Scores answers: exact numbers deterministically, everything else with an LLM judge.

- `parse_numbers` reads every number in a text, handling commas, `$`, `%`, accounting negatives in parentheses and scale words (thousand/k, million/M/mn, billion/B/bn).
- `numeric_match` accepts an answer when any number equals the gold amount within 0.5%, either as written or read at the gold's own scale (a bare "955,224" from a table in thousands).
- `GroqJudge` adapts the rate-limited Groq client to DeepEval's `DeepEvalBaseLLM`, returning a validated schema when DeepEval asks for structured output.
- `judge_metrics` builds DeepEval's faithfulness and answer-relevancy metrics at threshold 0.7, run synchronously so the client's pacing isn't bypassed.
- `citation_precision` asks the judge, one call per citation, whether each cited chunk supports the answer; a refusal without citations scores 1.0.
