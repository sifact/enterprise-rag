"""The answer pipeline: guard the question, search the role's passages, check the evidence,
drop passages carrying instructions, write a cited answer, check its citations.

Each refusal records why (blocked input, no evidence, unsupported answer, or the model's own
"not in sources"), so the UI can explain it and the evaluation can count it.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from contextlib import contextmanager

from enterprise_rag.config import RagConfig
from enterprise_rag.generation import PROMPT_VERSION
from enterprise_rag.guardrails import InjectionGuard, check_citations, filter_context
from enterprise_rag.retrieval.types import PipelineResponse, RetrievedChunk


class RagPipeline:
    def __init__(self, retriever, guard: InjectionGuard, generator, cfg: RagConfig,
                 name: str = "rag"):
        self.retriever, self.guard, self.generator, self.cfg = retriever, guard, generator, cfg
        self.name = name

    def retrieve(self, question: str, role: str, k: int) -> list[RetrievedChunk]:
        return self.retriever.search(question, role, k)

    def answer(self, question: str, role: str) -> PipelineResponse:
        stages: dict[str, float] = {}
        timed = _timer(stages)
        trace: dict = {"stages": stages, "removed": [], "top_score": None,
                       "refusal_reason": None, "prompt_version": PROMPT_VERSION,
                       "model": self.generator.model}

        def refuse(reason: str, retrieved=()) -> PipelineResponse:
            trace["refusal_reason"] = reason
            return PipelineResponse("", True, (), tuple(retrieved), None, trace)

        with timed("input_guard"):
            guard = self.guard.check(question, kind="question")
        trace["guard"] = {"flagged": guard.flagged, "score": guard.score, "reason": guard.reason}
        if guard.flagged:
            return refuse("blocked_input")

        with timed("search"):
            chunks = self.retriever.search(question, role, self.cfg.context_chunks)
        if chunks:
            trace["top_score"] = max(_strength(c) for c in chunks)
        if not chunks or trace["top_score"] < self.cfg.evidence_threshold:
            return refuse("no_evidence", chunks)

        with timed("context_guard"):
            kept, removed = filter_context(chunks, self.guard)
        trace["removed"] = [{"chunk_id": c.chunk_id, "doc_id": c.doc_id, "reason": why}
                            for c, why in removed]
        if not kept:
            return refuse("no_evidence", chunks)

        with timed("generate"):
            generated = self.generator.generate(question, role, kept)
        generated = check_citations(generated, len(kept))
        trace["used"] = [c.chunk_id for c in kept]
        if generated.refused:
            trace["refusal_reason"] = generated.reason or "not_in_sources"
        citations = tuple(kept[n - 1].chunk_id for n in generated.citations)
        return PipelineResponse(generated.answer, generated.refused, citations, tuple(chunks),
                                generated.usage, trace)


def _strength(chunk: RetrievedChunk) -> float:
    """Evidence strength: the reranker's score when there is one, else the search score."""
    return chunk.rerank_score if chunk.rerank_score is not None else chunk.score


def _timer(stages: dict[str, float]) -> Callable:
    @contextmanager
    def timed(name: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            stages[name] = round((time.perf_counter() - start) * 1000, 1)
    return timed
