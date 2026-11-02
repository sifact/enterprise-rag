"""Chunking and the search index: documents in, role-labelled searchable passages out."""

from enterprise_rag.indexing.chunking import Chunk, chunk_corpus, chunk_document, strip_hidden_text
from enterprise_rag.indexing.embedders import Embedders, FastEmbedders, SparseVec
from enterprise_rag.indexing.store import (
    DENSE,
    ROLE_FIELD,
    SPARSE,
    build_index,
    open_client,
    search_text,
)

__all__ = [
    "DENSE",
    "ROLE_FIELD",
    "SPARSE",
    "Chunk",
    "Embedders",
    "FastEmbedders",
    "SparseVec",
    "build_index",
    "chunk_corpus",
    "chunk_document",
    "open_client",
    "search_text",
    "strip_hidden_text",
]
