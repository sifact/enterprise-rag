"""The three local models behind search: dense embeddings, BM25 sparse vectors and a reranker.

They run on CPU through fastembed (ONNX), so the demo needs no GPU and no paid embedding API.
Everything else depends on the small `Embedders` protocol, so tests use a hash-based fake.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from enterprise_rag.config import RagConfig

BATCH_SIZE = 64


@dataclass(frozen=True)
class SparseVec:
    indices: list[int]
    values: list[float]


class Embedders(Protocol):
    dense_dim: int

    def dense(self, texts: Sequence[str]) -> list[list[float]]: ...
    def dense_query(self, text: str) -> list[float]: ...
    def sparse(self, texts: Sequence[str]) -> list[SparseVec]: ...
    def sparse_query(self, text: str) -> SparseVec: ...
    def rerank(self, query: str, texts: Sequence[str]) -> list[float]: ...


class FastEmbedders:
    """fastembed models, loaded on first use and cached under `models_cache_dir`."""

    def __init__(self, cfg: RagConfig):
        from fastembed import SparseTextEmbedding, TextEmbedding
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        cache = str(cfg.models_cache_dir)
        self._dense = TextEmbedding(cfg.embed_model, cache_dir=cache)
        self._sparse = SparseTextEmbedding(cfg.sparse_model, cache_dir=cache)
        self._reranker = TextCrossEncoder(cfg.rerank_model, cache_dir=cache)
        self.dense_dim = len(next(iter(self._dense.embed(["probe"]))))

    def dense(self, texts: Sequence[str]) -> list[list[float]]:
        return [v.tolist() for v in self._dense.embed(list(texts), batch_size=BATCH_SIZE)]

    def dense_query(self, text: str) -> list[float]:
        return next(iter(self._dense.query_embed(text))).tolist()

    def sparse(self, texts: Sequence[str]) -> list[SparseVec]:
        return [SparseVec(v.indices.tolist(), v.values.tolist())
                for v in self._sparse.embed(list(texts), batch_size=BATCH_SIZE)]

    def sparse_query(self, text: str) -> SparseVec:
        v = next(iter(self._sparse.query_embed(text)))
        return SparseVec(v.indices.tolist(), v.values.tolist())

    def rerank(self, query: str, texts: Sequence[str]) -> list[float]:
        return [float(s) for s in self._reranker.rerank(query, list(texts))]
