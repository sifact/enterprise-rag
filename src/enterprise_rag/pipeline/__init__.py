"""Named pipelines: retrieval variants and the full answer pipeline."""

from enterprise_rag.pipeline.rag import RagPipeline

_LAZY = {name: "enterprise_rag.pipeline.registry" for name in (
    "PIPELINE_NAMES", "RAG_RETRIEVER", "RETRIEVERS", "build_pipeline", "build_rag",
    "build_retriever", "collection_name",
)}

__all__ = [
    "PIPELINE_NAMES",
    "RAG_RETRIEVER",
    "RETRIEVERS",
    "RagPipeline",
    "build_pipeline",
    "build_rag",
    "build_retriever",
    "collection_name",
]


def __getattr__(name: str):
    """Heavy members load on first use, so the serverless API only imports what it needs."""
    if name in _LAZY:
        import importlib

        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
