"""BM25 over whole document pages with a role pre-filter: a smoke test for the harness.

It lets the evaluation run end to end before the real pipeline exists. Its numbers are a
floor to sanity-check the harness against, not a row of the ablation table.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

from rank_bm25 import BM25Okapi

from enterprise_rag.data import (
    DocumentRecord,
    load_doc_pages,
    load_fixture_pages,
    load_fixture_roles,
)
from enterprise_rag.retrieval.types import PipelineResponse, RetrievedChunk

_TOKEN = re.compile(r"\w+")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class ReferenceBM25:
    name = "reference-bm25"

    def __init__(
        self,
        manifest: Sequence[DocumentRecord],
        raw_dir: Path,
        fixtures_dir: Path | None = None,
    ):
        """Build one index per role up front, so a role's search never sees other chunks."""
        chunks: list[tuple[RetrievedChunk, tuple[str, ...]]] = []
        for rec in manifest:
            for page in load_doc_pages(rec, raw_dir):
                chunks.append((_chunk(rec.doc_id, page.page, page.text), rec.allowed_roles))
        if fixtures_dir is not None:
            roles = load_fixture_roles(fixtures_dir)
            for doc_id, pages in load_fixture_pages(fixtures_dir).items():
                for page in pages:
                    chunks.append((_chunk(doc_id, page.page, page.text), roles[doc_id]))

        all_roles = sorted({r for _, allowed in chunks for r in allowed})
        self._index: dict[str, tuple[BM25Okapi, list[RetrievedChunk]]] = {}
        for role in all_roles:
            visible = [c for c, allowed in chunks if role in allowed]
            self._index[role] = (BM25Okapi([tokenize(c.text) for c in visible]), visible)

    def retrieve(self, question: str, role: str, k: int) -> list[RetrievedChunk]:
        if role not in self._index:
            return []
        bm25, visible = self._index[role]
        scores = bm25.get_scores(tokenize(question))
        ranked = sorted(range(len(visible)), key=lambda i: scores[i], reverse=True)[:k]
        return [_with_score(visible[i], float(scores[i])) for i in ranked]

    def answer(self, question: str, role: str) -> PipelineResponse:
        """No generator: always refuses, so only the retrieval-side safety checks are meaningful."""
        return PipelineResponse(text="", refused=True, citations=(),
                                retrieved=tuple(self.retrieve(question, role, 10)), usage=None)


def _chunk(doc_id: str, page: int | None, text: str) -> RetrievedChunk:
    chunk_id = doc_id if page is None else f"{doc_id}#p{page}"
    return RetrievedChunk(doc_id, chunk_id, text, 0.0)


def _with_score(chunk: RetrievedChunk, score: float) -> RetrievedChunk:
    return RetrievedChunk(chunk.doc_id, chunk.chunk_id, chunk.text, score)
