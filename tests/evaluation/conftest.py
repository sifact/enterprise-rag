from dataclasses import replace

import pytest

from enterprise_rag.data import DocPage, DocumentRecord
from enterprise_rag.evaluation import Evidence, GoldenItem

ROLES = ("engineering", "hr", "marketing", "legal", "sales", "finance", "c_level")

ENG_TEXT = (
    "Every merge request needs one approval from a maintainer of the project before it can be "
    "merged, and the author must address every open thread first."
)
LEGAL_TEXT = (
    "Contracts above fifty thousand dollars need a review by the commercial legal team, "
    "which aims to respond within three business days of the request."
)


def record(doc_id: str, allowed: tuple[str, ...], path: str = "x.md") -> DocumentRecord:
    return DocumentRecord(doc_id, "handbook", path, doc_id, None, "x", allowed, "CC", "h")


@pytest.fixture
def manifest():
    return [
        record("handbook:eng", ("c_level", "engineering")),
        record("handbook:legal", ("c_level", "legal")),
    ]


@pytest.fixture
def doc_texts():
    return {"handbook:eng": [DocPage(None, ENG_TEXT)], "handbook:legal": [DocPage(None, LEGAL_TEXT)]}


@pytest.fixture
def item():
    return GoldenItem(
        id="eng-001",
        question="How many maintainer sign-offs does a change need?",
        asked_as="engineering",
        category="single_fact",
        expected_behavior="answer",
        reference_answer="One approval from a maintainer.",
        numeric_answer=None,
        gold_evidence=(Evidence("handbook:eng", ENG_TEXT[:100], None),),
        forbidden_doc_ids=(),
        split=None,
        notes="test",
    )


@pytest.fixture
def make_item(item):
    def _make(**changes):
        return replace(item, **changes)

    return _make
