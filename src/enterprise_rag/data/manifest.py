"""One manifest row per source document, carrying the access-control metadata.

Ingestion reads `allowed_roles` from here and copies it onto every chunk, so this is the
single place where a document's visibility is decided.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from enterprise_rag.config import DataConfig


@dataclass(frozen=True)
class DocumentRecord:
    doc_id: str
    source: str  # "handbook" | "sec" | "synthetic"
    path: str  # relative to raw_dir
    title: str
    source_url: str | None
    department: str  # owning department, or "general"
    allowed_roles: tuple[str, ...]
    license: str
    content_hash: str


def allowed_roles_for(owner_role: str | None, cfg: DataConfig) -> tuple[str, ...]:
    """Owner role plus the superuser; `None` (company-wide content) means every role."""
    if owner_role is None:
        return tuple(sorted(cfg.roles))
    return tuple(sorted({owner_role, cfg.superuser_role}))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_manifest(path: Path) -> list[DocumentRecord]:
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return [DocumentRecord(**{**r, "allowed_roles": tuple(r["allowed_roles"])}) for r in rows]


def write_manifest(path: Path, records: list[DocumentRecord], replace_sources: set[str]) -> None:
    """Replace only the rows of `replace_sources`, so one source can be re-fetched alone."""
    kept = [r for r in read_manifest(path) if r.source not in replace_sources]
    merged = sorted(kept + records, key=lambda r: r.doc_id)
    ids = [r.doc_id for r in merged]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate doc_id in manifest")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(asdict(r)) + "\n" for r in merged))
