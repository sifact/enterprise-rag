import pytest

from enterprise_rag.data import DocumentRecord
from enterprise_rag.retrieval import Pipeline, ReferenceBM25

ALL = ("c_level", "engineering", "finance", "hr", "legal", "marketing", "sales")
DOCS = {
    "handbook:eng": (("c_level", "engineering"),
                     "Kubernetes deploys roll out through canary clusters before production."),
    "handbook:legal": (("c_level", "legal"),
                       "Contracts need a signature from the commercial counsel before renewal."),
    "handbook:values": (ALL, "Our values are collaboration, results and transparency for all."),
}


@pytest.fixture
def bm25(tmp_path):
    manifest = []
    for doc_id, (roles, text) in DOCS.items():
        path = doc_id.split(":")[1] + ".md"
        (tmp_path / path).write_text(f"---\ntitle: {doc_id}\n---\n{text}\n")
        manifest.append(DocumentRecord(doc_id, "handbook", path, doc_id, None, "x", roles, "CC", "h"))
    return ReferenceBM25(manifest, tmp_path)


def doc_ids(chunks):
    return [c.doc_id for c in chunks]


def test_implements_pipeline(bm25):
    assert isinstance(bm25, Pipeline)
    assert bm25.answer("anything", "legal").refused


def test_role_prefilter_hides_other_departments(bm25):
    got = doc_ids(bm25.retrieve("kubernetes canary clusters deploys", "legal", k=10))
    assert "handbook:eng" not in got
    assert set(got) <= {"handbook:legal", "handbook:values"}


def test_c_level_sees_all(bm25):
    assert set(doc_ids(bm25.retrieve("contracts kubernetes values", "c_level", k=10))) == set(DOCS)


def test_general_doc_visible_to_every_role(bm25):
    for role in ALL:
        assert "handbook:values" in doc_ids(bm25.retrieve("values transparency", role, k=10))


def test_ranking_prefers_matching_doc(bm25):
    assert doc_ids(bm25.retrieve("commercial counsel signature", "c_level", k=3))[0] == (
        "handbook:legal"
    )
