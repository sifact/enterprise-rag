# judge.py

The LLM judge used by full evaluation runs.

- `GroqJudge` adapts the rate-limited Groq client (`openai/gpt-oss-120b`) to DeepEval's `DeepEvalBaseLLM`, returning a validated schema when DeepEval asks for structured output.
- `judge_metrics` builds DeepEval's faithfulness and answer-relevancy metrics at threshold 0.7, run synchronously so the client's pacing isn't bypassed.
- The judge is a different model family from the answer model (Qwen), so it isn't grading its own outputs.
- DeepEval is a heavy import, so this module is loaded only for judged evaluation runs; the web server never imports it (saves about 40 MB).
- Groq's free tier caps this model at 200,000 tokens a day, and a judged run over the 43 test questions needs more than that, so judged runs may need to be split across days.
