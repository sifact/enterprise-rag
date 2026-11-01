import pytest

from enterprise_rag.data import DocumentRecord
from enterprise_rag.evaluation import (
    DraftPlan,
    Passage,
    draft_all,
    draft_item,
    sample_passages,
    write_review_file,
)
from enterprise_rag.llm import LLMError, Usage

PASSAGE_TEXT = (
    "Every merge request needs one approval from a maintainer of the project before it can be "
    "merged. The author must resolve every open thread first, and the pipeline on the target "
    "branch has to be green. Maintainers are listed in the project's code owners file."
)
QUOTE = ("Every merge request needs one approval from a maintainer of the project before it "
         "can be merged.")


class FakeClient:
    model = "fake"

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def complete_json(self, system, user, temperature=0.0):
        self.calls += 1
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply, Usage(1, 1, 1.0)


def passage(pid="eng-fact-001"):
    return Passage(id=pid, category="single_fact", bucket="single_fact:engineering",
                   asked_as="engineering", doc_ids=("handbook:eng",), pages=(None,),
                   texts=(PASSAGE_TEXT,))


def reply(question="How many sign-offs does a change need before it lands?", quote=QUOTE):
    return {"question": question, "answer": "One maintainer approval.", "quotes": [quote]}


def test_draft_item_accepts_valid_draft():
    item = draft_item(passage(), FakeClient([reply()]))
    assert item is not None
    assert item.id == "eng-fact-001" and item.asked_as == "engineering"
    assert item.gold_evidence[0].doc_id == "handbook:eng"
    assert item.expected_behavior == "answer"
    assert "drafted" in item.notes


def test_draft_rejects_quote_not_in_passage():
    bad = reply(quote="Deploys happen every Tuesday after the release manager signs off on it.")
    assert draft_item(passage(), FakeClient([bad])) is None


def test_draft_rejects_copied_question():
    copied = reply(question="Does every merge request need one approval from a maintainer of "
                            "the project before it can be merged?")
    assert draft_item(passage(), FakeClient([copied])) is None


def test_draft_rejects_duplicate_question():
    seen = {"how many sign-offs does a change need before it lands?"}
    assert draft_item(passage(), FakeClient([reply()]), seen_questions=seen) is None


def test_invalid_json_draft_is_skipped():
    client = FakeClient([LLMError("bad json"), reply()])
    p1, p2 = passage("eng-fact-001"), passage("eng-fact-002")
    items = draft_all([p1, p2], client, {"single_fact:engineering": 1})
    assert [i.id for i in items] == ["eng-fact-002"]


def test_draft_all_stops_at_quota():
    client = FakeClient([reply(), reply(question="Who has to approve a merge request?")])
    items = draft_all([passage("a"), passage("b")], client, {"single_fact:engineering": 1})
    assert len(items) == 1 and client.calls == 1


def _write_pages(tmp_path):
    manifest = []
    words = [f"term{i}" for i in range(400)]
    for n in range(4):
        body = "\n\n".join(
            f"## Section {s}\n\n" + " ".join(words[(n * 7 + s * 13 + k) % 400] for k in range(120))
            for s in range(3)
        )
        (tmp_path / f"p{n}.md").write_text(f"---\ntitle: p{n}\n---\n{body}\n")
        manifest.append(DocumentRecord(f"handbook:engineering/p{n}", "handbook", f"p{n}.md",
                                       f"p{n}", None, "engineering",
                                       ("c_level", "engineering"), "CC", "h"))
    return manifest


def test_sampling_deterministic(tmp_path):
    manifest = _write_pages(tmp_path)
    plan = DraftPlan(single_fact_per_department=2, departments=("engineering",), general_page=0,
                     multi_hop=1, sec_lookup_10k=0, sec_lookup_10q=0)
    a = sample_passages(plan, manifest, tmp_path, seed=42)
    assert a == sample_passages(plan, manifest, tmp_path, seed=42)
    assert a != sample_passages(plan, manifest, tmp_path, seed=7)
    assert sum(p.category == "single_fact" for p in a) == 3  # 2 × 1.5 oversampling
    multi = [p for p in a if p.category == "multi_hop"]
    assert multi and all(len(set(p.doc_ids)) == 2 for p in multi)
    assert plan.quotas() == {"single_fact:engineering": 2, "multi_hop": 1}


def test_write_review_file(tmp_path):
    item = draft_item(passage(), FakeClient([reply()]))
    path = tmp_path / "review.md"
    write_review_file([item], path)
    text = path.read_text()
    assert "## eng-fact-001" in text and "- [ ] accept" in text and "- [ ] drop" in text


@pytest.mark.parametrize("bad", [{"question": "q"}, {"question": "q", "answer": "a", "quotes": []}])
def test_draft_rejects_incomplete_json(bad):
    assert draft_item(passage(), FakeClient([bad])) is None
