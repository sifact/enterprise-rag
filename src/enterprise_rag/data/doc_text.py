"""Plain text of each source document, split into pages, as the gold quotes refer to it.

Gold quotes are checked against this text, so it has to be one rendering used everywhere:
markdown without front matter, one entry per PDF page, one CSV page per spreadsheet sheet.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

from enterprise_rag.data.handbook_pages import split_front_matter
from enterprise_rag.data.manifest import DocumentRecord

FIXTURE_PREFIX = "fixture:"


@dataclass(frozen=True)
class DocPage:
    page: int | None  # 1-based PDF page or sheet number; None for single-page markdown
    text: str


def load_doc_pages(record: DocumentRecord, raw_dir: Path) -> list[DocPage]:
    return list(_load_path(raw_dir / record.path))


@cache
def _load_path(path: Path) -> tuple[DocPage, ...]:
    """Cached: the 10-K alone takes seconds to parse and is read once per golden item."""
    suffix = path.suffix.lower()
    if suffix == ".md":
        _, body = split_front_matter(path.read_text())
        return (DocPage(None, body),)
    if suffix == ".pdf":
        reader = PdfReader(path)
        return tuple(DocPage(i, page.extract_text() or "") for i, page in
                     enumerate(reader.pages, start=1))
    if suffix == ".xlsx":
        sheets = pd.read_excel(path, sheet_name=None)
        return tuple(DocPage(i, sheet_to_text(name, df)) for i, (name, df) in
                     enumerate(sheets.items(), start=1))
    raise ValueError(f"Unsupported document type: {path}")


def sheet_to_text(name: str, df: pd.DataFrame) -> str:
    """One sheet as `Sheet: <name>` plus CSV rows; computed gold quotes use the same rendering."""
    return f"Sheet: {name}\n" + df.to_csv(index=False)


def load_fixture_pages(fixtures_dir: Path) -> dict[str, list[DocPage]]:
    """Poisoned pages for indirect-injection runs, keyed `fixture:<stem>`."""
    return {
        FIXTURE_PREFIX + p.stem: [DocPage(None, split_front_matter(p.read_text())[1])]
        for p in sorted(fixtures_dir.glob("*.md"))
    }


def load_fixture_roles(fixtures_dir: Path) -> dict[str, tuple[str, ...]]:
    """`allowed_roles` from each fixture's front matter, keyed like `load_fixture_pages`."""
    return {
        FIXTURE_PREFIX + p.stem: tuple(split_front_matter(p.read_text())[0].get("allowed_roles", []))
        for p in sorted(fixtures_dir.glob("*.md"))
    }
