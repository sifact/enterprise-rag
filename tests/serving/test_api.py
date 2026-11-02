import json
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from enterprise_rag.config import load_rag_config
from enterprise_rag.llm import LLMError, Usage
from enterprise_rag.retrieval import PipelineResponse, RetrievedChunk
from enterprise_rag.serving import create_app

ROLES = ("engineering", "hr", "marketing", "legal", "sales", "finance", "c_level")
RAG = replace(load_rag_config(), rate_per_minute=6, rate_per_day=100, max_question_chars=500)
META = {"roles": [{"name": r, "label": r.title(), "documents": 1} for r in ROLES],
        "examples": {}, "corpus": {"documents": 275}}


class FakePipeline:
    name = "fake"

    def __init__(self, fail=False):
        self.calls, self.fail = [], fail

    def answer(self, question, role):
        self.calls.append((question, role))
        if self.fail:
            raise LLMError("groq down")
        chunk = RetrievedChunk("handbook:x", "handbook:x#c0001", "Leave is 16 weeks.", 0.9, None,
                               {"title": "Leave", "section": "Parental", "page": None,
                                "allowed_roles": ["c_level", role], "source_url": "https://h/x"})
        return PipelineResponse(f"Answer for {role} [1].", False, ("handbook:x#c0001",),
                                (chunk,), Usage(10, 5, 3.0),
                                {"stages": {"search": 5.0}, "removed": [], "top_score": 0.9,
                                 "refusal_reason": None, "guard": {"flagged": False,
                                                                   "score": 0.0, "reason": ""},
                                 "model": "fake-gen", "prompt_version": "answer-v1"})


def write_run(runs, name, split, mode, aggregates):
    runs.mkdir(exist_ok=True)
    (runs / f"2026-11-03-{name}-{split}-{mode}.json").write_text(json.dumps({
        "pipeline_name": name, "split": split, "mode": mode, "aggregates": aggregates,
        "golden_version": "v1", "started_at": "2026-11-03T00:00:00+00:00", "config": {},
        "items": []}))


@pytest.fixture
def make_client(tmp_path):
    def _make(pipeline=None, **cfg):
        app = create_app(pipeline or FakePipeline(), replace(RAG, **cfg), ROLES, META,
                         runs_dir=tmp_path / "runs", secret="test-secret")
        return TestClient(app)
    return _make


def signed_in(client, role="hr"):
    assert client.post("/api/session", json={"role": role}).status_code == 200
    return client


def test_meta_lists_roles(make_client):
    body = make_client().get("/api/meta").json()
    assert [r["name"] for r in body["roles"]] == list(ROLES)


def test_session_rejects_unknown_role(make_client):
    assert make_client().post("/api/session", json={"role": "intern"}).status_code == 422


def test_ask_requires_session(make_client):
    r = make_client().post("/api/ask", json={"question": "How long is leave?"})
    assert r.status_code == 401


def test_tampered_session_rejected(make_client):
    client = signed_in(make_client(), "hr")
    token = client.cookies.get("session")
    client.cookies.clear()
    client.cookies.set("session", token.replace("hr", "c_level", 1))
    assert client.post("/api/ask", json={"question": "Revenue?"}).status_code == 401


def test_signer_rejects_edited_expired_and_garbage_tokens():
    from enterprise_rag.serving.session import SessionSigner

    signer = SessionSigner(ROLES, "k", max_age_s=60)
    token = signer.issue("hr", now=1000)
    assert signer.verify(token, now=1010) == "hr"
    assert signer.verify(token.replace("hr", "c_level", 1), now=1010) is None
    assert signer.verify(token, now=2000) is None
    assert signer.verify("hr", now=1010) is None and signer.verify(None) is None


def test_body_role_ignored(make_client):
    pipeline = FakePipeline()
    client = signed_in(make_client(pipeline), "hr")
    r = client.post("/api/ask", json={"question": "Revenue?", "role": "c_level"})
    assert r.status_code == 200 and pipeline.calls == [("Revenue?", "hr")]
    assert r.json()["role"] == "hr"


@pytest.mark.parametrize("question", ["", "   ", "x" * 501])
def test_question_length_validated(make_client, question):
    r = signed_in(make_client()).post("/api/ask", json={"question": question})
    assert r.status_code == 422 and "detail" in r.json()


def test_ask_returns_answer_citations_and_trace(make_client):
    body = signed_in(make_client()).post("/api/ask", json={"question": "Leave?"}).json()
    assert body["answer"] == "Answer for hr [1]." and not body["refused"]
    assert body["citations"][0]["n"] == 1 and body["citations"][0]["title"] == "Leave"
    assert body["retrieved"][0]["cited"] is True
    assert body["timings"] == {"search": 5.0} and body["cached"] is False


def test_rate_limit_returns_429_after_6_per_minute(make_client):
    client = signed_in(make_client())
    codes = [client.post("/api/ask", json={"question": f"q{i}"}).status_code for i in range(7)]
    assert codes[:6] == [200] * 6 and codes[6] == 429


def test_repeat_question_served_from_cache(make_client):
    pipeline = FakePipeline()
    client = signed_in(make_client(pipeline))
    first = client.post("/api/ask", json={"question": "Leave?"}).json()
    second = client.post("/api/ask", json={"question": "  leave? "}).json()
    assert len(pipeline.calls) == 1 and second["cached"] is True
    assert second["answer"] == first["answer"]


def test_cache_is_per_role(make_client):
    pipeline = FakePipeline()
    client = make_client(pipeline)
    signed_in(client, "hr").post("/api/ask", json={"question": "Leave?"})
    signed_in(client, "legal").post("/api/ask", json={"question": "Leave?"})
    assert [role for _, role in pipeline.calls] == ["hr", "legal"]


def test_llm_outage_returns_503(make_client):
    r = signed_in(make_client(FakePipeline(fail=True))).post("/api/ask", json={"question": "q"})
    assert r.status_code == 503 and "try again" in r.json()["detail"].lower()


def test_results_endpoint_reads_test_runs_only(make_client, tmp_path):
    write_run(tmp_path / "runs", "hybrid", "test", "retrieval", {"ndcg@10": 0.9})
    write_run(tmp_path / "runs", "hybrid", "dev", "retrieval", {"ndcg@10": 0.5})
    body = make_client().get("/api/results").json()
    assert [r["pipeline"] for r in body["retrieval"]] == ["hybrid"]
    assert body["retrieval"][0]["ndcg@10"] == 0.9


def test_responses_never_contain_api_key(make_client, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_secret_value")
    client = signed_in(make_client())
    texts = [client.get("/api/meta").text, client.get("/api/results").text,
             client.post("/api/ask", json={"question": "Leave?"}).text]
    assert not any("gsk_secret_value" in t for t in texts)
