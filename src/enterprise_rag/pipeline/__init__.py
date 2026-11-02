"""Named pipelines: retrieval variants and the full answer pipeline."""

from enterprise_rag.pipeline.rag import RagPipeline
from enterprise_rag.pipeline.registry import (
    PIPELINE_NAMES,
    RAG_RETRIEVER,
    RETRIEVERS,
    build_pipeline,
    build_rag,
    build_retriever,
    collection_name,
)

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
