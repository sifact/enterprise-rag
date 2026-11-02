from types import SimpleNamespace

from qdrant_client import models

from enterprise_rag.indexing.chunking import Chunk
from enterprise_rag.indexing.cloud_store import build_cloud_index
from enterprise_rag.retrieval.cloud import CloudRetriever

DENSE, SPARSE = "sentence-transformers/all-minilm-l6-v2", "qdrant/bm25"


class RecordingClient:
    """Records calls; returns one canned point per query."""

    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            if name == "collection_exists":
                return False
            if name == "query_points":
                payload = {"doc_id": "handbook:x", "chunk_id": "handbook:x#c0000",
                           "text": "Leave is 16 weeks.", "title": "Leave", "section": "",
                           "page": None, "allowed_roles": ["c_level", "hr"],
                           "source_url": None, "context_header": "Leave", "department": "hr"}
                return SimpleNamespace(points=[SimpleNamespace(payload=payload, score=0.71)])
            return None
        return record


def role_of(flt: models.Filter) -> str:
    (cond,) = flt.must
    assert cond.key == "allowed_roles"
    return cond.match.value


def test_index_sends_text_for_server_side_embedding_and_indexes_roles():
    client = RecordingClient()
    chunk = Chunk("handbook:x#c0000", "handbook:x", "Leave", "S", None, "Leave is 16 weeks.",
                  "Leave > S", ("c_level", "hr"), "hr", None)
    assert build_cloud_index([chunk], client, "c", DENSE, SPARSE) == 1
    names = [c[0] for c in client.calls]
    assert names[:3] == ["collection_exists", "create_collection", "create_payload_index"]
    (_, _, upsert) = next(c for c in client.calls if c[0] == "upsert")
    vector = upsert["points"][0].vector
    assert vector["dense"] == models.Document(text="Leave > S\nLeave is 16 weeks.", model=DENSE)
    assert vector["bm25"].model == SPARSE
    assert upsert["points"][0].payload["allowed_roles"] == ["c_level", "hr"]


def test_hybrid_query_filters_every_prefetch_by_role():
    client = RecordingClient()
    r = CloudRetriever(client, "c", mode="hybrid", fusion="dbsf", dense_model=DENSE,
                       sparse_model=SPARSE)
    chunks = r.search("How long is parental leave?", "hr", k=6)
    (_, _, q) = [c for c in client.calls if c[0] == "query_points"][-1]
    assert role_of(q["query_filter"]) == "hr"
    assert [role_of(p.filter) for p in q["prefetch"]] == ["hr", "hr"]
    assert [p.query.model for p in q["prefetch"]] == [DENSE, SPARSE]
    assert q["query"].fusion == models.Fusion.DBSF
    assert chunks[0].chunk_id == "handbook:x#c0000" and chunks[0].meta["title"] == "Leave"


def test_evidence_is_top_dense_similarity_within_the_role():
    client = RecordingClient()
    r = CloudRetriever(client, "c", mode="hybrid", fusion="rrf", dense_model=DENSE,
                       sparse_model=SPARSE)
    assert r.evidence("How long is parental leave?", "legal") == 0.71
    (_, _, q) = [c for c in client.calls if c[0] == "query_points"][-1]
    assert q["using"] == "dense" and q["limit"] == 1 and role_of(q["query_filter"]) == "legal"
