"""Build any named pipeline the CLI, the evaluation and the API can run."""

from __future__ import annotations

from dataclasses import replace

from enterprise_rag.config import DataConfig, EvalConfig, RagConfig
from enterprise_rag.data import read_manifest
from enterprise_rag.generation import Generator
from enterprise_rag.guardrails import InjectionGuard, groq_scorer
from enterprise_rag.indexing import FastEmbedders, open_client, search_text
from enterprise_rag.llm import GroqClient
from enterprise_rag.pipeline.rag import RagPipeline
from enterprise_rag.retrieval import HybridRetriever, Pipeline, ReferenceBM25

SAFETY_SUFFIX = "_safety"
# Retrieval-only variants, each one change from its neighbour, for the ablation table.
RETRIEVERS: dict[str, dict] = {
    "dense": {"mode": "dense", "rerank": False},
    "bm25-chunks": {"mode": "sparse", "rerank": False},
    "hybrid": {"mode": "hybrid", "fusion": "rrf", "rerank": False},
    "hybrid-dbsf": {"mode": "hybrid", "fusion": "dbsf", "rerank": False},
    "hybrid-rerank": {"mode": "hybrid", "fusion": "rrf", "rerank": True},
}
# The deployed (Qdrant Cloud) variants: same comparison, server-side MiniLM + BM25 embeddings.
CLOUD_RETRIEVERS: dict[str, dict] = {
    "cloud-dense": {"mode": "dense", "fusion": "rrf"},
    "cloud-bm25": {"mode": "sparse", "fusion": "rrf"},
    "cloud-hybrid": {"mode": "hybrid", "fusion": "rrf"},
    "cloud-hybrid-dbsf": {"mode": "hybrid", "fusion": "dbsf"},
}
PIPELINE_NAMES = ("reference-bm25", *RETRIEVERS, "rag", *CLOUD_RETRIEVERS, "rag-cloud")
# Best retrieval variant on the dev split (nDCG@10 0.895); reranking lowered it (see ledger).
RAG_RETRIEVER = "hybrid-dbsf"


def collection_name(rag: RagConfig, safety: bool) -> str:
    """Safety runs and the demo search the collection that also holds the poisoned pages."""
    return rag.collection + (SAFETY_SUFFIX if safety else "")


def build_retriever(name: str, rag: RagConfig, safety: bool, client=None,
                    embedders=None) -> HybridRetriever:
    return HybridRetriever(
        client or open_client(rag), collection_name(rag, safety),
        embedders or FastEmbedders(rag), name=name,
        prefetch_limit=rag.prefetch_limit, rerank_candidates=rag.rerank_candidates,
        **RETRIEVERS[name],
    )


def build_pipeline(name: str, data: DataConfig, rag: RagConfig, ev: EvalConfig,
                   safety: bool) -> Pipeline:
    if name == "reference-bm25":
        return ReferenceBM25(read_manifest(data.manifest_path), data.raw_dir,
                             fixtures_dir=ev.fixtures_dir if safety else None)
    if name in RETRIEVERS:
        return build_retriever(name, rag, safety)
    if name == "rag":
        return build_rag(rag, ev, safety)
    if name in CLOUD_RETRIEVERS or name == "rag-cloud":
        from enterprise_rag.retrieval.cloud import CloudRetriever
        from enterprise_rag.serving.cloud_app import build_cloud_rag, cloud_client

        collection = collection_name(replace(rag, collection=rag.cloud_collection), safety)
        if name == "rag-cloud":
            return build_cloud_rag(cloud_client(), collection)
        return CloudRetriever(cloud_client(), collection, dense_model=rag.cloud_dense_model,
                              sparse_model=rag.cloud_sparse_model,
                              prefetch_limit=rag.prefetch_limit, name=name,
                              **CLOUD_RETRIEVERS[name])
    raise ValueError(f"Unknown pipeline {name!r}; choose from {PIPELINE_NAMES}")


def build_rag(rag: RagConfig, ev: EvalConfig, safety: bool, client=None,
              embedders=None) -> RagPipeline:
    """The full answer pipeline over the chosen retriever, with Groq guard and generator."""
    generator = Generator(GroqClient(rag.generator_model, ev.tokens_per_minute,
                                     extra_body={"reasoning_format": "hidden"}))
    guard = InjectionGuard(groq_scorer(GroqClient(rag.guard_model, ev.tokens_per_minute)),
                           rag.guard_threshold)
    embedders = embedders or FastEmbedders(rag)
    retriever = build_retriever(RAG_RETRIEVER, rag, safety, client, embedders)

    def evidence(question: str, role: str, chunks) -> float:
        """Cross-encoder relevance of the best passage: separated answerable from must-refuse
        dev questions better (AUC 0.82) than dense similarity (0.78)."""
        return max(embedders.rerank(question, [search_text(c.meta["context_header"], c.text)
                                               for c in chunks]))

    return RagPipeline(retriever, guard, generator, rag, evidence=evidence)
