"""Ask the answer model for a short, cited answer and parse its JSON reply."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from enterprise_rag.generation.prompt import build_messages
from enterprise_rag.llm import GroqClient, LLMError, Usage
from enterprise_rag.retrieval.types import RetrievedChunk

ANSWER_MAX_TOKENS = 600


@dataclass(frozen=True)
class Generated:
    answer: str
    citations: tuple[int, ...]  # 1-based source numbers as the model cited them
    refused: bool
    reason: str
    usage: Usage | None


def _ints(values) -> tuple[int, ...]:
    out = []
    for v in values or ():
        try:
            out.append(int(v))
        except (TypeError, ValueError):
            continue
    return tuple(dict.fromkeys(out))


class Generator:
    def __init__(self, client: GroqClient, max_tokens: int = ANSWER_MAX_TOKENS):
        self.client, self.max_tokens = client, max_tokens

    @property
    def model(self) -> str:
        return self.client.model

    def generate(self, question: str, role: str, chunks: Sequence[RetrievedChunk]) -> Generated:
        system, user = build_messages(question, role, chunks)
        data, usage = self.client.complete_json(system, user, temperature=0.0,
                                                max_tokens=self.max_tokens)
        refused = bool(data.get("refused"))
        answer = str(data.get("answer") or "").strip()
        if not refused and not answer:
            raise LLMError(f"{self.model}: reply has neither an answer nor a refusal: {data}")
        return Generated(answer=answer, citations=_ints(data.get("citations")), refused=refused,
                         reason=str(data.get("reason") or ""), usage=usage)
