"""Write chunks into an embedded Qdrant collection with dense and BM25 vectors.

Each point carries the chunk's text and `allowed_roles` as payload; search filters on that
field inside every query. The collection is rebuilt from scratch on each run, so an index can
never mix chunks from two chunker or model versions.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from dataclasses import asdict

from qdrant_client import QdrantClient, models

from enterprise_rag.config import RagConfig
from enterprise_rag.indexing.chunking import Chunk
from enterprise_rag.indexing.embedders import Embedders

UPSERT_BATCH = 128
DENSE, SPARSE = "dense", "bm25"
ROLE_FIELD = "allowed_roles"
log = logging.getLogger(__name__)


def open_client(cfg: RagConfig) -> QdrantClient:
    """On-disk embedded Qdrant; one process at a time may open it."""
    cfg.index_dir.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(cfg.index_dir))


def search_text(chunk_header: str, text: str) -> str:
    """What gets embedded and keyword-indexed: the header gives a short chunk its context."""
    return f"{chunk_header}\n{text}"


def build_index(chunks: Sequence[Chunk], embedders: Embedders, client: QdrantClient,
                collection: str) -> int:
    if client.collection_exists(collection):
        client.delete_collection(collection)
    client.create_collection(
        collection,
        vectors_config={DENSE: models.VectorParams(size=embedders.dense_dim,
                                                   distance=models.Distance.COSINE)},
        sparse_vectors_config={SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)},
    )
    client.create_payload_index(collection, ROLE_FIELD, models.PayloadSchemaType.KEYWORD)
    for start in range(0, len(chunks), UPSERT_BATCH):
        batch = chunks[start : start + UPSERT_BATCH]
        texts = [search_text(c.context_header, c.text) for c in batch]
        dense, sparse = embedders.dense(texts), embedders.sparse(texts)
        client.upsert(collection, [
            models.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, c.chunk_id)),
                vector={DENSE: d, SPARSE: models.SparseVector(indices=s.indices, values=s.values)},
                payload={**asdict(c), ROLE_FIELD: list(c.allowed_roles)},
            )
            for c, d, s in zip(batch, dense, sparse, strict=True)
        ])
        log.info("indexed %d/%d chunks", min(start + UPSERT_BATCH, len(chunks)), len(chunks))
    return len(chunks)
