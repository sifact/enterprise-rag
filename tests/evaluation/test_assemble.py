from collections import Counter
from dataclasses import replace

import pytest

from enterprise_rag.data import DocPage
from enterprise_rag.evaluation import (
    Evidence,
    UnreviewedDraftError,
    assemble,
    derive_c_level,
    derive_cross_role,
    parse_review_decisions,
    reviewed_drafts,
    write_review_file,
)

from .conftest import ROLES, record

DEPTS = ("engineering", "hr", "marketing", "legal", "sales", "finance")
TEXT = " ".join(f"word{i}" for i in range(200))
QUOTE = " ".join(f"word{i}" for i in range(20))
SPEC_COUNTS = {"single_fact": 24, "general_page": 6, "multi_hop": 6, "sec_lookup": 8,
               "spreadsheet_lookup": 6, "cross_source_finance": 4, "c_level": 4,
               "cross_role": 12, "out_of_scope": 6, "direct_injection": 5,
               "indirect_injection": 3}


@pytest.fixture
def world(make_item):
    manifest = [record(f"doc:{d}", tuple(sorted({d, "c_level"}))) for d in DEPTS]
    manifest.append(record("doc:general", ROLES))
    doc_texts = {r.doc_id: [DocPage(None, TEXT)] for r in manifest}
    doc_texts["fixture:faq"] = [DocPage(None, TEXT)]

    def answer(id_, cat, role, doc):
        return make_item(id=id_, category=cat, asked_as=role,
                         gold_evidence=(Evidence(doc, QUOTE),), notes="drafted")

    drafts = [answer(f"{d}-{k}", "single_fact", d, f"doc:{d}") for d in DEPTS for k in range(4)]
    drafts += [answer(f"gen-{k}", "general_page", DEPTS[k], "doc:general") for k in range(6)]
    drafts += [answer(f"mh-{k}", "multi_hop", d, f"doc:{d}") for k, d in enumerate(DEPTS)]
    drafts += [answer(f"sec-{k}", "sec_lookup", "finance", "doc:finance") for k in range(8)]
    computed = [answer(f"xlsx-{k}", "spreadsheet_lookup", "finance", "doc:finance")
                for k in range(6)]
    computed += [answer(f"cross-{k}", "cross_source_finance", "finance", "doc:finance")
                 for k in range(2)]
    refuse = {"expected_behavior": "refuse", "reference_answer": "", "gold_evidence": ()}
    handwritten = [make_item(id=f"oos-{k}", category="out_of_scope", **refuse) for k in range(6)]
    handwritten += [make_item(id=f"dir-{k}", category="direct_injection", **refuse)
                    for k in range(5)]
    handwritten += [answer(f"ind-{k}", "indirect_injection", "legal", "fixture:faq")
                    for k in range(3)]
    handwritten += [answer(f"cross-h{k}", "cross_source_finance", "finance", "doc:finance")
                    for k in range(2)]
    return drafts, computed, handwritten, manifest, doc_texts


def test_derive_cross_role_never_uses_c_level_or_a_role_that_can_see(world):
    drafts, computed, _, manifest, _ = world
    allowed = {r.doc_id: set(r.allowed_roles) for r in manifest}
    items = derive_cross_role(drafts + computed, manifest, ROLES, "c_level", seed=42)
    assert len(items) == 12
    for item in items:
        assert item.asked_as != "c_level"
        assert item.expected_behavior == "refuse" and not item.gold_evidence
        assert all(item.asked_as not in allowed[d] for d in item.forbidden_doc_ids)
        assert "twin: " in item.notes


def test_every_non_c_level_role_appears_in_cross_role(world):
    drafts, computed, _, manifest, _ = world
    items = derive_cross_role(drafts + computed, manifest, ROLES, "c_level", seed=42)
    assert {i.asked_as for i in items} == set(DEPTS)


def test_derive_c_level_reasks_department_items(world):
    drafts, computed, _, manifest, _ = world
    items = derive_c_level(drafts + computed, manifest, "c_level", seed=42)
    assert len(items) == 4
    assert {i.asked_as for i in items} == {"c_level"}
    assert {i.category for i in items} == {"c_level"}
    assert len({i.gold_evidence[0].doc_id for i in items}) == 4  # four different departments


def test_assemble_counts_by_category(world):
    drafts, computed, handwritten, manifest, doc_texts = world
    items = assemble(drafts, computed, handwritten, manifest, doc_texts, ROLES, "c_level",
                     seed=42)
    assert Counter(i.category for i in items) == SPEC_COUNTS
    assert len(items) == 84
    assert all(i.split in {"dev", "test"} for i in items)


def test_assemble_refuses_unreviewed_drafts(world, tmp_path):
    drafts = world[0][:3]
    path = tmp_path / "review.md"
    write_review_file(drafts, path)
    sections = path.read_text().split("\n## ")
    sections[1] = sections[1].replace("- [ ] accept", "- [x] accept")
    sections[3] = sections[3].replace("- [ ] drop", "- [x] drop")  # drafts[1] left undecided
    path.write_text("\n## ".join(sections))
    decisions = parse_review_decisions(path)
    assert decisions[drafts[0].id] == ("accept", "")
    with pytest.raises(UnreviewedDraftError, match=drafts[1].id):
        reviewed_drafts(drafts, decisions)


def test_reviewed_drafts_keeps_accept_and_edit_with_note(world, tmp_path):
    drafts = world[0][:3]
    path = tmp_path / "review.md"
    write_review_file(drafts, path)
    sections = path.read_text().split("\n## ")
    sections[1] = sections[1].replace("- [ ] accept", "- [x] accept")
    sections[2] = sections[2].replace("- [ ] edit", "- [x] edit").replace(
        "Review note:", "Review note: shortened the answer")
    sections[3] = sections[3].replace("- [ ] drop", "- [x] drop")
    path.write_text("\n## ".join(sections))
    kept = reviewed_drafts(drafts, parse_review_decisions(path))
    assert [i.id for i in kept] == [drafts[0].id, drafts[1].id]
    assert "edited in review: shortened the answer" in kept[1].notes
    assert replace(kept[0], notes=drafts[0].notes) == drafts[0]
