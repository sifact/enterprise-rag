"""Search one role's passages with dense, keyword or hybrid retrieval, then rerank.

The role filter sits inside every Qdrant query, including each prefetch of a hybrid search,
so passages the role can't read are never scored, fused or shown to the reranker.
"""

from __future__ import annotations

from typing import Literal

from qdrant_client import QdrantClient, models

from enterprise_rag.indexing import DENSE, ROLE_FIELD, SPARSE, Embedders, search_text
from enterprise_rag.retrieval.types import PipelineResponse, RetrievedChunk

SearchMode = Literal["dense", "sparse", "hybrid"]
Fusion = Literal["rrf", "dbsf"]
_FUSION = {"rrf": models.Fusion.RRF, "dbsf": models.Fusion.DBSF}
META_FIELDS = ("title", "section", "page", "allowed_roles", "source_url", "context_header",
               "department")


class HybridRetriever:
    def __init__(self, client: QdrantClient, collection: str, embedders: Embedders,
                 mode: SearchMode = "hybrid", fusion: Fusion = "rrf", rerank: bool = True,
                 prefetch_limit: int = 50, rerank_candidates: int = 40, name: str = "hybrid"):
        self.client, self.collection, self.embedders = client, collection, embedders
        self.mode, self.fusion, self.rerank = mode, fusion, rerank
        self.prefetch_limit, self.rerank_candidates = prefetch_limit, rerank_candidates
        self.name = name

    def retrieve(self, question: str, role: str, k: int) -> list[RetrievedChunk]:
        return self.search(question, role, k)

    def search(self, question: str, role: str, k: int) -> list[RetrievedChunk]:
        role_filter = models.Filter(must=[
            models.FieldCondition(key=ROLE_FIELD, match=models.MatchValue(value=role))])
        limit = max(k, self.rerank_candidates) if self.rerank else k
        points = self._query(question, role_filter, limit)
        chunks = [RetrievedChunk(p.payload["doc_id"], p.payload["chunk_id"], p.payload["text"],
                                 float(p.score),
                                 meta={f: p.payload.get(f) for f in META_FIELDS})
                  for p in points]
        if self.rerank and chunks:
            scores = self.embedders.rerank(
                question, [search_text(c.meta["context_header"], c.text) for c in chunks])
            chunks = [RetrievedChunk(c.doc_id, c.chunk_id, c.text, c.score, s, c.meta)
                      for c, s in sorted(zip(chunks, scores, strict=True),
                                         key=lambda cs: cs[1], reverse=True)]
        return chunks[:k]

    def _query(self, question: str, role_filter: models.Filter, limit: int):
        if self.mode == "dense":
            kwargs = {"query": self._dense(question), "using": DENSE}
        elif self.mode == "sparse":
            kwargs = {"query": self._sparse(question), "using": SPARSE}
        else:
            kwargs = {
                "prefetch": [
                    models.Prefetch(query=self._dense(question), using=DENSE,
                                    filter=role_filter, limit=self.prefetch_limit),
                    models.Prefetch(query=self._sparse(question), using=SPARSE,
                                    filter=role_filter, limit=self.prefetch_limit),
                ],
                "query": models.FusionQuery(fusion=_FUSION[self.fusion]),
            }
        return self.client.query_points(self.collection, query_filter=role_filter, limit=limit,
                                        with_payload=True, **kwargs).points

    def _dense(self, question: str) -> list[float]:
        return self.embedders.dense_query(question)

    def _sparse(self, question: str) -> models.SparseVector:
        v = self.embedders.sparse_query(question)
        return models.SparseVector(indices=v.indices, values=v.values)

    def answer(self, question: str, role: str) -> PipelineResponse:
        """Retrieval-only pipeline: never writes an answer."""
        return PipelineResponse(text="", refused=True, citations=(),
                                retrieved=tuple(self.search(question, role, 10)), usage=None)
