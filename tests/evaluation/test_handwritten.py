import re
from collections import Counter

import pytest

from enterprise_rag.config import PROJECT_ROOT, load_config, load_eval_config
from enterprise_rag.data import load_doc_pages, load_fixture_pages, read_manifest
from enterprise_rag.evaluation import load_handwritten, validate_golden

HANDWRITTEN = PROJECT_ROOT / "eval" / "golden" / "handwritten.yaml"
OVERRIDE_MARKERS = ("ignore", "you are now", "as c_level", "system prompt")


@pytest.fixture(scope="module")
def items():
    return load_handwritten(HANDWRITTEN)


def test_category_counts(items):
    counts = Counter(i.category for i in items)
    assert counts == {"out_of_scope": 6, "direct_injection": 5, "indirect_injection": 3,
                      "cross_source_finance": 2}


def test_direct_injections_attempt_override(items):
    for item in items:
        if item.category == "direct_injection":
            assert any(m in item.question.lower() for m in OVERRIDE_MARKERS), item.id


def test_indirect_canaries_are_planted_in_fixtures(items):
    fixtures = load_fixture_pages(load_eval_config().fixtures_dir)
    for item in items:
        if item.category == "indirect_injection":
            canary = re.search(r"CANARY-[\w-]+", item.notes).group()
            (ev,) = item.gold_evidence
            assert canary in fixtures[ev.doc_id][0].text, item.id


def test_handwritten_items_load_and_validate(items):
    cfg = load_config()
    if not cfg.manifest_path.exists():
        pytest.skip("corpus not fetched")
    manifest = read_manifest(cfg.manifest_path)
    needed = {ev.doc_id for i in items for ev in i.gold_evidence}
    doc_texts = {r.doc_id: load_doc_pages(r, cfg.raw_dir) for r in manifest if r.doc_id in needed}
    doc_texts |= load_fixture_pages(load_eval_config().fixtures_dir)
    validate_golden(items, manifest, doc_texts, cfg.roles)
