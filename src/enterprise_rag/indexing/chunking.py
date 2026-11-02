"""Cut documents into passages that keep their structure and their access labels.

Each chunk copies its document's `allowed_roles`, so the search index can filter by role
before ranking. Splits follow headings, then paragraphs, then sentences, so a passage never
ends mid-sentence; spreadsheet chunks repeat the header row so every piece is readable alone.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from enterprise_rag.config import RagConfig
from enterprise_rag.data import (
    DocPage,
    DocumentRecord,
    load_doc_pages,
    load_fixture_pages,
    load_fixture_roles,
)

# Text a reader never sees must not reach the model (hidden instructions live there).
_HIDDEN = (
    re.compile(r"<!--.*?-->", re.DOTALL),
    re.compile(r"^\[[^\]]*\]:\s*#.*$", re.MULTILINE),
    re.compile(r"<(\w+)[^>]*style=\"[^\"]*display\s*:\s*none[^\"]*\"[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE),
)
_HEADING = re.compile(r"^(#{1,4})\s+(.+?)\s*#*\s*$", re.MULTILINE)
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[*_])")
_LINE_ITEM = re.compile(r"^\s*([-*+]|\d+[.)]|\|)\s")


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    section: str
    page: int | None
    text: str
    context_header: str
    allowed_roles: tuple[str, ...]
    department: str
    source_url: str | None


@dataclass(frozen=True)
class _Unit:
    text: str
    is_line: bool  # list item or table row: joined with a newline, not a space


def strip_hidden_text(text: str) -> str:
    for pattern in _HIDDEN:
        text = pattern.sub("", text)
    return text


def _units(text: str, max_words: int) -> list[_Unit]:
    """Sentences for prose, whole lines for lists and tables; overlong units cut by words."""
    units: list[_Unit] = []
    for para in re.split(r"\n\s*\n", text):
        lines = [ln.strip() for ln in para.splitlines() if ln.strip()]
        if not lines:
            continue
        if any(_LINE_ITEM.match(ln) for ln in lines):
            units += [_Unit(ln, True) for ln in lines]
        else:
            units += [_Unit(s, False) for s in _SENTENCE_BREAK.split(" ".join(lines)) if s]
    out = []
    for u in units:
        words = u.text.split()
        if len(words) <= max_words:
            out.append(u)
        else:  # text without sentence ends (e.g. a PDF table): fixed word windows
            out += [_Unit(" ".join(words[i : i + max_words]), u.is_line)
                    for i in range(0, len(words), max_words)]
    return out


def _join(units: Sequence[_Unit]) -> str:
    text = units[0].text
    for prev, cur in zip(units, units[1:], strict=False):
        text += ("\n" if prev.is_line or cur.is_line else " ") + cur.text
    return text


def _pack(units: Sequence[_Unit], size: int, overlap: int) -> list[str]:
    """Greedy packing up to `size` words; each new chunk starts with up to `overlap` words
    of whole units from the end of the previous one."""
    chunks: list[str] = []
    cur: list[_Unit] = []
    cur_words = 0
    for u in units:
        n = len(u.text.split())
        if cur and cur_words + n > size:
            chunks.append(_join(cur))
            carry: list[_Unit] = []
            carried = 0
            for prev in reversed(cur):
                pw = len(prev.text.split())
                if carried + pw > overlap:
                    break
                carry.insert(0, prev)
                carried += pw
            cur, cur_words = carry, carried
        cur.append(u)
        cur_words += n
    if cur:
        chunks.append(_join(cur))
    return chunks


def _markdown_sections(text: str) -> list[tuple[str, str]]:
    """(section path, body) pairs; the path joins nested headings with ' > '."""
    sections: list[tuple[str, str]] = []
    stack: list[tuple[int, str]] = []
    pos, path = 0, ""
    for m in _HEADING.finditer(text):
        sections.append((path, text[pos : m.start()]))
        level = len(m.group(1))
        stack = [(lvl, name) for lvl, name in stack if lvl < level] + [(level, m.group(2))]
        path = " > ".join(name for _, name in stack)
        pos = m.end()
    sections.append((path, text[pos:]))
    return [(p, body) for p, body in sections if body.strip()]


def _merged_sections(text: str, cfg: RagConfig) -> list[tuple[str, str]]:
    """Pack heading sections into chunks. Small neighbouring sections share a chunk (named
    after the first one) so short stubs don't flood search results; each section's heading
    is kept as the first line of its text."""
    out: list[tuple[str, str]] = []
    buf: list[_Unit] = []
    buf_section = ""

    def flush() -> None:
        for t in _pack(buf, cfg.chunk_words, cfg.chunk_overlap_words):
            out.append((buf_section, t))
        buf.clear()

    for section, body in _markdown_sections(text):
        units = _units(body, cfg.chunk_words)
        if section:
            units.insert(0, _Unit(section.rsplit(" > ", 1)[-1], True))
        words = sum(len(u.text.split()) for u in units)
        buf_words = sum(len(u.text.split()) for u in buf)
        if buf and (buf_words >= cfg.min_chunk_words or buf_words + words > cfg.chunk_words):
            flush()
        if not buf:
            buf_section = section
        buf.extend(units)
    if buf:
        flush()
    return out


def _sheet_pieces(text: str, rows_per: int, overlap: int) -> tuple[str, list[str]]:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    name, header, rows = lines[0].removeprefix("Sheet: "), lines[1], lines[2:]
    pieces, start, step = [], 0, max(1, rows_per - overlap)
    while True:
        pieces.append("\n".join([lines[0], header, *rows[start : start + rows_per]]))
        if start + rows_per >= len(rows):
            return name, pieces
        start += step


def chunk_document(record: DocumentRecord, pages: Sequence[DocPage],
                   cfg: RagConfig) -> list[Chunk]:
    suffix = Path(record.path).suffix.lower()
    pieces: list[tuple[str, int | None, str, str]] = []  # section, page, header, text
    for page in pages:
        text = strip_hidden_text(page.text)
        if not text.strip():
            continue
        if suffix == ".xlsx":
            name, sheet_texts = _sheet_pieces(text, cfg.sheet_rows_per_chunk,
                                              cfg.sheet_overlap_rows)
            pieces += [(name, page.page, f"{record.title} > {name}", t) for t in sheet_texts]
        elif suffix == ".pdf":
            for t in _pack(_units(text, cfg.chunk_words), cfg.chunk_words,
                           cfg.chunk_overlap_words):
                pieces.append(("", page.page, f"{record.title} > page {page.page}", t))
        else:
            for section, t in _merged_sections(text, cfg):
                header = f"{record.title} > {section}" if section else record.title
                pieces.append((section, page.page, header, t))
    return [
        Chunk(chunk_id=f"{record.doc_id}#c{i:04d}", doc_id=record.doc_id, title=record.title,
              section=section, page=page, text=text, context_header=header,
              allowed_roles=tuple(record.allowed_roles), department=record.department,
              source_url=record.source_url)
        for i, (section, page, header, text) in enumerate(pieces)
    ]


def chunk_corpus(manifest: Sequence[DocumentRecord], raw_dir: Path, cfg: RagConfig,
                 fixtures_dir: Path | None = None) -> list[Chunk]:
    """Every manifest document, plus the poisoned fixture pages for safety runs."""
    chunks = [c for rec in manifest for c in chunk_document(rec, load_doc_pages(rec, raw_dir), cfg)]
    if fixtures_dir is not None:
        roles = load_fixture_roles(fixtures_dir)
        for doc_id, pages in load_fixture_pages(fixtures_dir).items():
            stem = doc_id.split(":", 1)[1]
            rec = DocumentRecord(doc_id, "fixture", f"{stem}.md",
                                 stem.replace("-", " ").capitalize(), None, "fixture",
                                 roles[doc_id], "test fixture", "")
            chunks += chunk_document(rec, pages, cfg)
    return chunks
