"""Answer quality: exact numeric match and citation precision (the DeepEval judge is in judge.py).

Numbers are compared deterministically after scale normalization, so finance answers don't
depend on an LLM judge. The judge (a different model family from the generator) is used for
faithfulness, relevancy and per-citation support.
"""

from __future__ import annotations

import re

from enterprise_rag.evaluation.golden import GoldenItem
from enterprise_rag.llm import GroqClient
from enterprise_rag.retrieval.types import PipelineResponse

CITATION_PROMPT_VERSION = "citation-v1"
CITATION_SYSTEM = (
    "You check citations in an answer. Given an ANSWER and one cited SOURCE passage, decide "
    "whether the passage supports at least one claim the answer makes. Reply with JSON "
    '{"supported": true|false}. Version: ' + CITATION_PROMPT_VERSION
)

_SCALES = {"thousand": 1e3, "k": 1e3, "million": 1e6, "mn": 1e6, "m": 1e6,
           "billion": 1e9, "bn": 1e9, "b": 1e9}
_NUMBER = re.compile(
    r"(?P<open>\()?\s*(?P<neg>-)?\$?\s*"
    r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"(?:\s*(?P<pct>%)|\s*(?P<scale>thousand|million|billion|bn|mn|k|m|b)\b)?"
    r"\s*(?P<close>\))?",
    re.IGNORECASE,
)


def parse_numbers(text: str) -> list[float]:
    """Every number in the text, with scale words applied and accounting negatives."""
    values = []
    for m in _NUMBER.finditer(text):
        value = float(m["num"].replace(",", ""))
        if m["scale"]:
            value *= _SCALES[m["scale"].lower()]
        if m["neg"] or (m["open"] and m["close"]):
            value = -value
        values.append(value)
    return values


def _close(a: float, b: float, tolerance: float) -> bool:
    return abs(a - b) <= tolerance * abs(b)


def numeric_match(item: GoldenItem, answer_text: str, tolerance: float) -> bool:
    """True if any number in the answer equals the gold amount, read either as written or
    in the gold's own unit scale (e.g. a bare "955,224" when the table is in thousands)."""
    if item.numeric_answer is None:
        return False
    target = item.numeric_answer.value * item.numeric_answer.scale
    return any(
        _close(n, target, tolerance) or _close(n * item.numeric_answer.scale, target, tolerance)
        for n in parse_numbers(answer_text)
    )


def citation_precision(item: GoldenItem, response: PipelineResponse, judge: GroqClient) -> float:
    """Share of cited chunks that support the answer, one judge call per citation."""
    if not response.citations:
        return 1.0 if response.refused else 0.0
    by_id = {c.chunk_id: c for c in response.retrieved}
    supported = 0
    for chunk_id in response.citations:
        chunk = by_id.get(chunk_id)
        if chunk is None:
            continue  # citing something that wasn't retrieved is unsupported
        data, _ = judge.complete_json(
            CITATION_SYSTEM, f"ANSWER:\n{response.text}\n\nSOURCE:\n{chunk.text}"
        )
        supported += bool(data.get("supported"))
    return supported / len(response.citations)
