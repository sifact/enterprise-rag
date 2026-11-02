"""Role-filtered hybrid search against Qdrant Cloud, with server-side embeddings.

Light enough for a serverless function: no local models. The role filter sits inside every
prefetch, exactly as in the local retriever, so other roles' passages are never scored.
"""

from __future__ import annotations

from typing import Literal

from qdrant_client import QdrantClient, models

from enterprise_rag.retrieval.types import PipelineResponse, RetrievedChunk

DENSE, SPARSE, ROLE_FIELD = "dense", "bm25", "allowed_roles"
META_FIELDS = ("title", "section", "page", "allowed_roles", "source_url", "context_header",
               "department")
_FUSION = {"rrf": models.Fusion.RRF, "dbsf": models.Fusion.DBSF}


def _role_filter(role: str) -> models.Filter:
    return models.Filter(must=[models.FieldCondition(key=ROLE_FIELD,
                                                     match=models.MatchValue(value=role))])


class CloudRetriever:
    def __init__(self, client: QdrantClient, collection: str,
                 mode: Literal["dense", "sparse", "hybrid"], fusion: Literal["rrf", "dbsf"],
                 dense_model: str, sparse_model: str, prefetch_limit: int = 50,
                 name: str = "cloud-hybrid"):
        self.client, self.collection, self.mode, self.fusion = client, collection, mode, fusion
        self.dense_model, self.sparse_model = dense_model, sparse_model
        self.prefetch_limit, self.name = prefetch_limit, name

    def _doc(self, text: str, model: str) -> models.Document:
        return models.Document(text=text, model=model)

    def search(self, question: str, role: str, k: int) -> list[RetrievedChunk]:
        flt = _role_filter(role)
        if self.mode == "dense":
            kwargs = {"query": self._doc(question, self.dense_model), "using": DENSE}
        elif self.mode == "sparse":
            kwargs = {"query": self._doc(question, self.sparse_model), "using": SPARSE}
        else:
            kwargs = {
                "prefetch": [
                    models.Prefetch(query=self._doc(question, self.dense_model), using=DENSE,
                                    filter=flt, limit=self.prefetch_limit),
                    models.Prefetch(query=self._doc(question, self.sparse_model), using=SPARSE,
                                    filter=flt, limit=self.prefetch_limit),
                ],
                "query": models.FusionQuery(fusion=_FUSION[self.fusion]),
            }
        points = self.client.query_points(self.collection, query_filter=flt, limit=k,
                                          with_payload=True, **kwargs).points
        return [RetrievedChunk(p.payload["doc_id"], p.payload["chunk_id"], p.payload["text"],
                               float(p.score), meta={f: p.payload.get(f) for f in META_FIELDS})
                for p in points]

    def retrieve(self, question: str, role: str, k: int) -> list[RetrievedChunk]:
        return self.search(question, role, k)

    def evidence(self, question: str, role: str) -> float:
        """Cosine similarity of the closest passage the role may read (the relevance check)."""
        points = self.client.query_points(self.collection,
                                          query=self._doc(question, self.dense_model),
                                          using=DENSE, query_filter=_role_filter(role), limit=1,
                                          with_payload=False).points
        return float(points[0].score) if points else 0.0

    def answer(self, question: str, role: str) -> PipelineResponse:
        """Retrieval-only use (ablations): never writes an answer."""
        return PipelineResponse("", True, (), tuple(self.search(question, role, 10)), None)
