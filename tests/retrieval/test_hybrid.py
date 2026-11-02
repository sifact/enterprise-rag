import pytest
from qdrant_client import QdrantClient

from enterprise_rag.indexing import Chunk, build_index
from enterprise_rag.retrieval import HybridRetriever, Pipeline

DOCS = [
    ("handbook:eng", ("c_level", "engineering"), "Kubernetes deploys roll out through canary clusters."),
    ("handbook:legal", ("c_level", "legal"), "Contracts need commercial counsel signature before renewal."),
    ("handbook:values", ("c_level", "engineering", "legal"), "Our values are collaboration and results."),
]


@pytest.fixture
def index(fake_embedders):
    client = QdrantClient(":memory:")
    chunks = [Chunk(f"{d}#c0000", d, d, "S", None, text, f"{d} > S", roles, "x", None)
              for d, roles, text in DOCS]
    build_index(chunks, fake_embedders, client, "t")
    return client


def retriever(index, fake_embedders, mode="hybrid", rerank=False):
    return HybridRetriever(index, "t", fake_embedders, mode=mode, rerank=rerank,
                           prefetch_limit=10, rerank_candidates=10, name=f"{mode}-test")


@pytest.mark.parametrize("mode", ["dense", "sparse", "hybrid"])
def test_role_filter_applied_in_every_mode(index, fake_embedders, mode):
    r = retriever(index, fake_embedders, mode)
    got = [c.doc_id for c in r.retrieve("kubernetes canary deploys clusters", "legal", k=5)]
    assert "handbook:eng" not in got
    assert set(got) <= {"handbook:legal", "handbook:values"}


def test_unknown_role_returns_nothing(index, fake_embedders):
    assert retriever(index, fake_embedders).retrieve("contracts", "intern", k=5) == []


def test_c_level_sees_everything(index, fake_embedders):
    got = {c.doc_id for c in retriever(index, fake_embedders, "dense").retrieve("x", "c_level", 5)}
    assert got == {d for d, _, _ in DOCS}


def test_rerank_reorders_by_cross_encoder_score(index, fake_embedders):
    r = retriever(index, fake_embedders, rerank=True)
    got = r.search("collaboration results values", "c_level", k=3)
    assert got[0].doc_id == "handbook:values"
    assert got[0].rerank_score >= got[1].rerank_score
    assert got[0].meta["title"] == "handbook:values"
    assert got[0].meta["allowed_roles"] == ["c_level", "engineering", "legal"]


def test_is_a_pipeline_that_refuses_to_answer(index, fake_embedders):
    r = retriever(index, fake_embedders)
    assert isinstance(r, Pipeline)
    assert r.answer("anything", "legal").refused
