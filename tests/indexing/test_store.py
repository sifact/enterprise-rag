from qdrant_client import QdrantClient

from enterprise_rag.indexing import Chunk, build_index


def chunk(i, doc="handbook:legal/x", roles=("c_level", "legal"), text="contract renewal rules"):
    return Chunk(f"{doc}#c{i:04d}", doc, "Title", "Section", None, f"{text} {i}",
                 "Title > Section", roles, "legal", None)


def test_build_index_stores_payload_and_role_filterable(fake_embedders):
    client = QdrantClient(":memory:")
    n = build_index([chunk(0), chunk(1, doc="handbook:eng/y", roles=("c_level", "engineering"))],
                    fake_embedders, client, "t")
    assert n == 2
    points, _ = client.scroll("t", limit=10, with_payload=True)
    payload = {p.payload["chunk_id"]: p.payload for p in points}
    assert payload["handbook:legal/x#c0000"]["allowed_roles"] == ["c_level", "legal"]
    assert payload["handbook:legal/x#c0000"]["context_header"] == "Title > Section"
    info = client.get_collection("t")
    assert set(info.config.params.vectors) == {"dense"}
    assert set(info.config.params.sparse_vectors) == {"bm25"}


def test_rebuild_replaces_collection(fake_embedders):
    client = QdrantClient(":memory:")
    build_index([chunk(0), chunk(1)], fake_embedders, client, "t")
    build_index([chunk(0)], fake_embedders, client, "t")
    assert client.count("t").count == 1
