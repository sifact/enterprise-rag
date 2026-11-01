"""Decide whether a chunk contains a gold quote, independent of how the corpus was chunked.

Quotes come from markdown, PDF text and CSV, and chunks may cut a quote in two, so both
sides are normalized first and a chunk that holds most of a quote still counts.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from typing import TYPE_CHECKING

from rapidfuzz import fuzz

if TYPE_CHECKING:  # golden.py imports this module to validate quotes
    from enterprise_rag.evaluation.golden import Evidence

NGRAM = 5
_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_HTML_TAG = re.compile(r"<[^>]+>")
_HYPHEN_BREAK = re.compile(r"(\w)-\s*\n\s*(\w)")
_MARKUP = re.compile(r"[*_`|#>~]")
_SPACE = re.compile(r"\s+")
_SMART = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                        "–": "-", "—": "-"})


def normalize_text(text: str) -> str:
    """Lowercase plain text with markdown, HTML, PDF hyphenation and odd spacing removed."""
    text = unicodedata.normalize("NFKC", text).translate(_SMART)
    text = _HYPHEN_BREAK.sub(r"\1\2", text)
    text = _LINK.sub(r"\1", text)
    text = _HTML_TAG.sub(" ", text)
    text = _MARKUP.sub("", text)
    return _SPACE.sub(" ", text).strip().lower()


def _ngrams(words: list[str], n: int) -> list[tuple[str, ...]]:
    n = min(n, len(words))
    return [tuple(words[i : i + n]) for i in range(len(words) - n + 1)]


def _ngram_coverage(quote: str, text: str) -> float:
    """Share of the quote's word n-grams present in the text; robust to a cut-off quote."""
    q_grams = _ngrams(quote.split(), NGRAM)
    if not q_grams:
        return 0.0
    t_grams = set(_ngrams(text.split(), NGRAM))
    return sum(g in t_grams for g in q_grams) / len(q_grams)


def quote_match_score(quote: str, text: str) -> float:
    """In [0, 1]: how much of the quote appears, in order, in the text."""
    q, t = normalize_text(quote), normalize_text(text)
    if not q or not t:
        return 0.0
    coverage = _ngram_coverage(q, t)
    if len(t) < len(q):
        # A fuzzy partial match would score a short fragment of the quote as a full hit.
        return coverage
    return max(fuzz.partial_ratio(q, t) / 100, coverage)


def quote_in_text(quote: str, text: str, threshold: float) -> bool:
    return quote_match_score(quote, text) >= threshold


def chunk_is_relevant(
    chunk_doc_id: str, chunk_text: str, gold: Sequence[Evidence], threshold: float
) -> bool:
    """Relevant only if the chunk comes from a gold document and holds one of its quotes."""
    return any(
        ev.doc_id == chunk_doc_id and quote_in_text(ev.quote, chunk_text, threshold) for ev in gold
    )
