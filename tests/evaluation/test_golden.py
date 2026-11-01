import pytest

from enterprise_rag.evaluation import (
    GoldenValidationError,
    NumericAnswer,
    assign_splits,
    load_golden,
    save_golden,
    validate_golden,
)

from .conftest import ROLES


def test_round_trip_save_load(tmp_path, make_item):
    items = [make_item(), make_item(id="eng-002", numeric_answer=NumericAnswer(955224, "USD", 1000))]
    path = tmp_path / "golden.jsonl"
    save_golden(path, items)
    assert load_golden(path) == items


def test_assign_splits_stratified_and_deterministic(make_item):
    items = [make_item(id=f"a-{i}", category="single_fact") for i in range(10)]
    items += [make_item(id=f"b-{i}", category="general_page") for i in range(10)]
    split = assign_splits(items, seed=42)
    for cat in ("single_fact", "general_page"):
        splits = {i.split for i in split if i.category == cat}
        assert splits == {"dev", "test"}
    assert assign_splits(items, seed=42) == split
    assert assign_splits(items, seed=7) != split


def test_validate_accepts_good_item(item, manifest, doc_texts):
    validate_golden([item], manifest, doc_texts, ROLES)


def test_validate_rejects_bad_role_and_category(make_item, manifest, doc_texts):
    bad = [make_item(id="bad-role", asked_as="ceo"), make_item(id="bad-cat", category="trivia")]
    with pytest.raises(GoldenValidationError) as exc:
        validate_golden(bad, manifest, doc_texts, ROLES)
    assert "bad-role" in str(exc.value) and "bad-cat" in str(exc.value)


def test_validate_requires_quote_length_10_to_60_words(make_item, manifest, doc_texts):
    from enterprise_rag.evaluation import Evidence

    short = make_item(id="short", gold_evidence=(Evidence("handbook:eng", "one approval", None),))
    with pytest.raises(GoldenValidationError, match="short"):
        validate_golden([short], manifest, doc_texts, ROLES)


def test_validate_cross_role_item_must_be_unseeable(make_item, manifest, doc_texts):
    common = {
        "category": "cross_role", "expected_behavior": "refuse", "reference_answer": "",
        "gold_evidence": (), "forbidden_doc_ids": ("handbook:eng",),
    }
    seeable = make_item(id="leaky", asked_as="engineering", **common)
    with pytest.raises(GoldenValidationError, match="leaky"):
        validate_golden([seeable], manifest, doc_texts, ROLES)
    validate_golden([make_item(id="ok", asked_as="legal", **common)], manifest, doc_texts, ROLES)
