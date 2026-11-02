"""Spot prompt injection in questions and in retrieved passages.

Two signals: a prompt-injection classifier (Llama Prompt Guard 2 on Groq) and a few regex
rules for the attacks it can miss, such as claiming another role. If the classifier is
unreachable the rules still run, so an outage weakens the guard instead of disabling it.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from typing import Literal

from enterprise_rag.llm import GroqClient, LLMError
from enterprise_rag.retrieval.types import RetrievedChunk

GUARD_MAX_CHARS = 2000  # Prompt Guard reads at most 512 tokens
CHECK_WORKERS = 6
_SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")
Kind = Literal["question", "passage"]

# (reason, pattern, applies to passages too?)
_RULES: tuple[tuple[str, re.Pattern, bool], ...] = (
    ("instruction_override", re.compile(
        r"\b(ignore|disregard|forget)\b.{0,40}\b(instructions?|rules|filters?|previous|above)\b",
        re.IGNORECASE | re.DOTALL), True),
    ("prompt_extraction", re.compile(r"\bsystem\s+(prompt|override|message)\b", re.IGNORECASE), True),
    ("role_play", re.compile(r"\b(you are now|admin mode|developer mode|jailbreak)\b", re.IGNORECASE), True),
    ("role_claim", re.compile(
        r"\b(as|i am|i'm)\s+(the\s+|a\s+|an\s+)?(c[_ -]?level|cfo|ceo|cto|admin(istrator)?)\b",
        re.IGNORECASE), False),
)


@dataclass(frozen=True)
class GuardResult:
    flagged: bool
    score: float  # classifier probability of injection; 0.0 when unavailable
    reason: str


def heuristic_flags(text: str, kind: Kind = "question") -> list[str]:
    """Rule names the text trips. Role claims only count in questions: documents may name roles."""
    return [name for name, pattern, in_passages in _RULES
            if (kind == "question" or in_passages) and pattern.search(text)]


def groq_scorer(client: GroqClient) -> Callable[[str], float]:
    def score(text: str) -> float:
        return client.classify(text[:GUARD_MAX_CHARS])
    return score


class InjectionGuard:
    def __init__(self, scorer: Callable[[str], float] | None, threshold: float):
        self.scorer, self.threshold = scorer, threshold

    def check(self, text: str, kind: Kind = "question") -> GuardResult:
        rules = heuristic_flags(text, kind)
        score, note = 0.0, ""
        if self.scorer is not None:
            try:
                score = float(self.scorer(text))
            except (LLMError, ValueError) as exc:
                note = f"classifier unavailable ({type(exc).__name__})"
        if rules:
            return GuardResult(True, score, rules[0])
        if score >= self.threshold:
            return GuardResult(True, score, "classifier")
        return GuardResult(False, score, note)


@dataclass(frozen=True)
class ContextCheck:
    kept: list[RetrievedChunk]  # passages given to the model (cleaned ones included)
    removed: list[tuple[RetrievedChunk, str]]  # dropped whole, with the reason
    cleaned: list[tuple[RetrievedChunk, str]]  # kept after cutting instruction sentences


def _cut_instructions(text: str) -> str | None:
    """The text without sentences that trip a rule, or None if no sentence did."""
    sentences = _SENTENCE.split(text)
    kept = [s for s in sentences if not heuristic_flags(s, kind="passage")]
    return " ".join(kept).strip() if len(kept) < len(sentences) else None


def filter_context(chunks: Sequence[RetrievedChunk], guard: InjectionGuard) -> ContextCheck:
    """Keep clean passages; cut planted instruction sentences out of flagged ones when a rule
    finds them and the rest then passes; drop the passage entirely otherwise."""
    kept, removed, cleaned = [], [], []
    with ThreadPoolExecutor(max_workers=CHECK_WORKERS) as pool:  # one classifier call each
        results = list(pool.map(lambda c: guard.check(c.text, kind="passage"), chunks))
    for chunk, result in zip(chunks, results, strict=True):
        if not result.flagged:
            kept.append(chunk)
            continue
        rest = _cut_instructions(chunk.text)
        if rest and not guard.check(rest, kind="passage").flagged:
            cleaned_chunk = replace(chunk, text=rest)
            kept.append(cleaned_chunk)
            cleaned.append((cleaned_chunk, result.reason))
        else:
            removed.append((chunk, result.reason))
    return ContextCheck(kept, removed, cleaned)
