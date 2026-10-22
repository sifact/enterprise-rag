"""Parsing and sampling of GitLab Handbook markdown pages (pure functions, no I/O beyond reads).

Many handbook pages are stubs: a title plus a list of links or a Hugo shortcode. They make
poor retrieval targets and poor golden-set sources, so pages are filtered by prose word
count before sampling.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

HANDBOOK_SITE = "https://handbook.gitlab.com"

_FRONT_MATTER = re.compile(r"\A(---|\+\+\+)\n(.*?)\n\1\n", re.DOTALL)
_SHORTCODE = re.compile(r"\{\{[<%].*?[%>]\}\}", re.DOTALL)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_HTML_TAG = re.compile(r"<[^>]+>")
_LINK_TARGET = re.compile(r"\]\([^)]*\)")
_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")


@dataclass(frozen=True)
class HandbookPage:
    rel_path: str  # relative to the handbook content root, e.g. "engineering/foo.md"
    title: str
    word_count: int


def split_front_matter(text: str) -> tuple[dict, str]:
    """Return (front matter, body). TOML front matter is rare in the handbook; its keys are skipped."""
    m = _FRONT_MATTER.match(text)
    if not m:
        return {}, text
    meta: dict = {}
    if m.group(1) == "---":
        try:
            meta = yaml.safe_load(m.group(2)) or {}
        except yaml.YAMLError:
            meta = {}
    return (meta if isinstance(meta, dict) else {}), text[m.end() :]


def prose_word_count(body: str) -> int:
    """Count words a reader would see: shortcodes, HTML and link URLs don't count."""
    for pattern in (_SHORTCODE, _HTML_COMMENT, _HTML_TAG, _LINK_TARGET):
        body = pattern.sub(" ", body)
    return len(_WORD.findall(body))


def parse_page(path: Path, content_root: Path) -> HandbookPage:
    meta, body = split_front_matter(path.read_text(encoding="utf-8", errors="replace"))
    rel = path.relative_to(content_root).as_posix()
    title = str(meta.get("title") or path.stem.replace("-", " ").strip("_ ").title())
    return HandbookPage(rel_path=rel, title=title, word_count=prose_word_count(body))


def page_url(rel_path: str) -> str:
    """Hugo maps `a/b.md` to /handbook/a/b/ and `a/_index.md` to /handbook/a/."""
    parts = rel_path.removesuffix(".md").split("/")
    if parts[-1] in ("_index", "index"):
        parts = parts[:-1]
    p = "/".join(parts)
    return f"{HANDBOOK_SITE}/handbook/{p}/" if p else f"{HANDBOOK_SITE}/handbook/"


def eligible_pages(content_root: Path, folders: tuple[str, ...], min_words: int) -> list[HandbookPage]:
    """All pages under `folders` with enough prose, in a stable (sorted) order."""
    pages = []
    for folder in folders:
        for path in sorted((content_root / folder).rglob("*.md")):
            page = parse_page(path, content_root)
            if page.word_count >= min_words:
                pages.append(page)
    return sorted(pages, key=lambda p: p.rel_path)


def sample_pages(pages: list[HandbookPage], k: int, seed: int, section: str) -> list[HandbookPage]:
    """Seed per section, so resizing one section doesn't reshuffle the others."""
    if len(pages) < k:
        raise ValueError(f"Section '{section}' has {len(pages)} eligible pages, config asks for {k}")
    rng = random.Random(f"{seed}:{section}")
    return sorted(rng.sample(pages, k), key=lambda p: p.rel_path)
