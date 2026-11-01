from math import log2

import pytest

from enterprise_rag.evaluation import (
    Evidence,
    doc_hit_at_k,
    evidence_recall_at_k,
    hit_at_k,
    mrr_at_k,
    ndcg_at_k,
    relevance_vector,
)
from enterprise_rag.retrieval import RetrievedChunk

REL = [False, True, False, True]
Q1 = "every merge request needs one approval from a maintainer of the project before merging"
Q2 = "contracts above fifty thousand dollars need a review by the commercial legal team first"


def chunk(doc_id, text):
    return RetrievedChunk(doc_id, doc_id, text, 1.0)


def test_rank_metrics_on_known_vector():
    assert hit_at_k(REL, 1) == 0
    assert hit_at_k(REL, 2) == 1
    assert mrr_at_k(REL, 10) == 0.5
    assert ndcg_at_k(REL, 10) == pytest.approx((1 / log2(3) + 1 / log2(5)) / (1 + 1 / log2(3)))


def test_all_false_scores_zero():
    rel = [False] * 5
    assert hit_at_k(rel, 5) == mrr_at_k(rel, 5) == ndcg_at_k(rel, 5) == 0


def test_mrr_respects_k():
    assert mrr_at_k(REL, 1) == 0


def test_evidence_recall_and_doc_hit(make_item):
    item = make_item(gold_evidence=(Evidence("a", Q1), Evidence("b", Q2)))
    chunks = [chunk("a", "intro " + Q1), chunk("b", "unrelated text about something else")]
    assert relevance_vector(item, chunks, 0.8) == [True, False]
    assert evidence_recall_at_k(item, chunks, 10, 0.8) == 0.5
    assert doc_hit_at_k(item, chunks, 10) == 1
    assert doc_hit_at_k(item, [chunk("c", Q1)], 10) == 0
