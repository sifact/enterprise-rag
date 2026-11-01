"""The contract every retrieval/answer pipeline meets so the harness can score it.

The asking role is always passed in by the caller, the way an authenticated session would
supply it; a pipeline never reads the role from the question text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from enterprise_rag.llm import Usage


@dataclass(frozen=True)
class RetrievedChunk:
    doc_id: str
    chunk_id: str
    text: str
    score: float


@dataclass(frozen=True)
class PipelineResponse:
    text: str
    refused: bool
    citations: tuple[str, ...]  # chunk IDs the answer cites
    retrieved: tuple[RetrievedChunk, ...]
    usage: Usage | None


@runtime_checkable
class Pipeline(Protocol):
    name: str

    def retrieve(self, question: str, role: str, k: int) -> list[RetrievedChunk]: ...

    def answer(self, question: str, role: str) -> PipelineResponse: ...
