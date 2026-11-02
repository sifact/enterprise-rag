"""Named pipelines: retrieval variants and the full answer pipeline."""

from enterprise_rag.pipeline.registry import (
    PIPELINE_NAMES,
    RETRIEVERS,
    build_pipeline,
    build_retriever,
    collection_name,
)

__all__ = ["PIPELINE_NAMES", "RETRIEVERS", "build_pipeline", "build_retriever", "collection_name"]
