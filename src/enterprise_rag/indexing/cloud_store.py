"""Write chunks to a Qdrant Cloud collection; Qdrant computes the embeddings server-side.

Text goes up as `models.Document`, and Qdrant Cloud Inference turns it into a MiniLM dense
vector and a BM25 sparse vector, so neither indexing nor the deployed API runs a local model.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from dataclasses import asdict

from qdrant_client import QdrantClient, models

from enterprise_rag.indexing.chunking import Chunk
from enterprise_rag.indexing.store import DENSE, ROLE_FIELD, SPARSE, search_text

CLOUD_BATCH = 64
MINILM_DIM = 384
log = logging.getLogger(__name__)


def open_cloud_client(url: str, api_key: str) -> QdrantClient:
    """`cloud_inference=True` makes Qdrant Cloud embed `Document` text instead of the client."""
    return QdrantClient(url=url, api_key=api_key, cloud_inference=True, timeout=120)


def build_cloud_index(chunks: Sequence[Chunk], client: QdrantClient, collection: str,
                      dense_model: str, sparse_model: str) -> int:
    if client.collection_exists(collection):
        client.delete_collection(collection)
    client.create_collection(
        collection,
        vectors_config={DENSE: models.VectorParams(size=MINILM_DIM,
                                                   distance=models.Distance.COSINE)},
        sparse_vectors_config={SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)},
    )
    # On a real Qdrant server the keyword index makes the role filter cheap at any scale.
    client.create_payload_index(collection, ROLE_FIELD, models.PayloadSchemaType.KEYWORD)
    for start in range(0, len(chunks), CLOUD_BATCH):
        batch = chunks[start : start + CLOUD_BATCH]
        client.upsert(collection, points=[
            models.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, c.chunk_id)),
                vector={
                    DENSE: models.Document(text=search_text(c.context_header, c.text),
                                           model=dense_model),
                    SPARSE: models.Document(text=search_text(c.context_header, c.text),
                                            model=sparse_model),
                },
                payload={**asdict(c), ROLE_FIELD: list(c.allowed_roles)},
            )
            for c in batch
        ])
        log.info("uploaded %d/%d chunks", min(start + CLOUD_BATCH, len(chunks)), len(chunks))
    return len(chunks)
