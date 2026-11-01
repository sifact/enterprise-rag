"""Golden set, evidence matching, metrics and the evaluation harness."""

from enterprise_rag.evaluation.doc_text import (
    DocPage,
    load_doc_pages,
    load_fixture_pages,
    load_fixture_roles,
    sheet_to_text,
)
from enterprise_rag.evaluation.evidence import (
    chunk_is_relevant,
    normalize_text,
    quote_in_text,
    quote_match_score,
)
from enterprise_rag.evaluation.golden import (
    CATEGORIES,
    Evidence,
    GoldenItem,
    GoldenValidationError,
    NumericAnswer,
    assign_splits,
    item_from_dict,
    load_golden,
    save_golden,
    validate_golden,
    word_count,
)

__all__ = [
    "CATEGORIES",
    "DocPage",
    "Evidence",
    "GoldenItem",
    "GoldenValidationError",
    "NumericAnswer",
    "assign_splits",
    "chunk_is_relevant",
    "item_from_dict",
    "load_doc_pages",
    "load_fixture_pages",
    "load_fixture_roles",
    "load_golden",
    "normalize_text",
    "quote_in_text",
    "quote_match_score",
    "save_golden",
    "sheet_to_text",
    "validate_golden",
    "word_count",
]
