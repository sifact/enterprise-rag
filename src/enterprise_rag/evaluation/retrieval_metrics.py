"""Rank metrics over one retrieved list, using quote matching as the relevance label.

Relevance comes from `chunk_is_relevant`, never chunk IDs, so runs with different chunking
stay comparable. All metrics use binary relevance.
"""

from __future__ import annotations

from collections.abc import Sequence
from math import log2

from enterprise_rag.evaluation.evidence import chunk_is_relevant, quote_in_text
from enterprise_rag.evaluation.golden import GoldenItem
from enterprise_rag.retrieval.types import RetrievedChunk


def relevance_vector(item: GoldenItem, chunks: Sequence[RetrievedChunk],
                     threshold: float) -> list[bool]:
    return [chunk_is_relevant(c.doc_id, c.text, item.gold_evidence, threshold) for c in chunks]


def hit_at_k(rel: Sequence[bool], k: int) -> float:
    return float(any(rel[:k]))


def mrr_at_k(rel: Sequence[bool], k: int) -> float:
    for rank, is_rel in enumerate(rel[:k], start=1):
        if is_rel:
            return 1 / rank
    return 0.0


def ndcg_at_k(rel: Sequence[bool], k: int) -> float:
    """Binary gains, log2 discount; the ideal order is the same hits moved to the top."""
    dcg = sum(1 / log2(i + 2) for i, r in enumerate(rel[:k]) if r)
    n_hits = sum(rel[:k])
    idcg = sum(1 / log2(i + 2) for i in range(n_hits))
    return dcg / idcg if idcg else 0.0


def evidence_recall_at_k(item: GoldenItem, chunks: Sequence[RetrievedChunk], k: int,
                         threshold: float) -> float:
    """Share of gold quotes found in at least one of the top-k chunks of the right document."""
    if not item.gold_evidence:
        return 0.0
    top = chunks[:k]
    covered = sum(
        any(c.doc_id == ev.doc_id and quote_in_text(ev.quote, c.text, threshold) for c in top)
        for ev in item.gold_evidence
    )
    return covered / len(item.gold_evidence)


def doc_hit_at_k(item: GoldenItem, chunks: Sequence[RetrievedChunk], k: int) -> float:
    """Sanity check alongside quote matching: did any gold document show up at all?"""
    gold_docs = {ev.doc_id for ev in item.gold_evidence}
    return float(any(c.doc_id in gold_docs for c in chunks[:k]))
