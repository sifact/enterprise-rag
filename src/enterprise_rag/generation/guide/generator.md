# generator.py

Calls the answer model and turns its JSON reply into a `Generated` result.

- Uses the Groq client with the configured answer model (`qwen/qwen3.8-27b`), temperature 0, at most 600 output tokens, and the model's reasoning text hidden.
- The reply must be JSON with `answer`, `citations`, `refused` and `reason`; citations are cleaned to unique integers and anything unreadable is dropped.
- A reply that neither answers nor refuses raises `LLMError`, so the pipeline treats it like an outage instead of showing an empty answer.
- Token usage and latency from the API are kept on the result for the cost and latency metrics.
- Checking that each cited number actually exists is left to `guardrails/output_check.py`, so generation stays a thin, testable wrapper.
