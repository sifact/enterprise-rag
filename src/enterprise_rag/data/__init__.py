"""Corpus acquisition: handbook pages, SEC filings and synthetic spreadsheets, plus the manifest."""

from enterprise_rag.data.handbook import fetch_handbook
from enterprise_rag.data.manifest import (
    DocumentRecord,
    allowed_roles_for,
    read_manifest,
    write_manifest,
)
from enterprise_rag.data.sec import FetchError, fetch_sec
from enterprise_rag.data.synthetic import build_workbooks, fetch_synthetic

__all__ = [
    "DocumentRecord",
    "FetchError",
    "allowed_roles_for",
    "build_workbooks",
    "fetch_handbook",
    "fetch_sec",
    "fetch_synthetic",
    "read_manifest",
    "write_manifest",
]
