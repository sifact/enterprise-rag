"""The LLM judge: DeepEval's faithfulness and relevancy metrics, run on Groq.

Kept apart from the other metrics because DeepEval is a heavy import; the web server never
loads this module, only evaluation runs that use a judge do.
"""

from __future__ import annotations

from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.models import DeepEvalBaseLLM

from enterprise_rag.llm import GroqClient

JUDGE_THRESHOLD = 0.7


class GroqJudge(DeepEvalBaseLLM):
    """Lets DeepEval metrics call our rate-limited Groq client instead of OpenAI."""

    def __init__(self, client: GroqClient):
        self.client = client
        super().__init__(model=client.model)

    def load_model(self):
        return self.client

    def generate(self, prompt: str, schema=None):
        if schema is not None:
            data, _ = self.client.complete_json("Reply with JSON only.", prompt)
            return schema.model_validate(data)
        text, _ = self.client.complete_text("You are a careful evaluator.", prompt)
        return text

    async def a_generate(self, prompt: str, schema=None):
        return self.generate(prompt, schema)

    def get_model_name(self) -> str:
        return self.client.model


def judge_metrics(judge: GroqJudge) -> list:
    """Synchronous metrics: the client is already paced, so async fan-out would only hit 429s."""
    return [
        FaithfulnessMetric(threshold=JUDGE_THRESHOLD, model=judge, async_mode=False),
        AnswerRelevancyMetric(threshold=JUDGE_THRESHOLD, model=judge, async_mode=False),
    ]
