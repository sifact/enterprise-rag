"""Retrieval pipelines and the protocol the evaluation harness calls."""

from enterprise_rag.llm import Usage
from enterprise_rag.retrieval.types import Pipeline, PipelineResponse, RetrievedChunk

_LAZY = {
    "HybridRetriever": "enterprise_rag.retrieval.hybrid",
    "ReferenceBM25": "enterprise_rag.retrieval.reference_bm25",
}

__all__ = ["HybridRetriever", "Pipeline", "PipelineResponse", "ReferenceBM25", "RetrievedChunk", "Usage"]


def __getattr__(name: str):
    """Heavy members load on first use, so the serverless API only imports what it needs."""
    if name in _LAZY:
        import importlib

        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
