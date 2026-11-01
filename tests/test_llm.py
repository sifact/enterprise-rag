import json

import pytest

from enterprise_rag.config import load_eval_config
from enterprise_rag.llm import GroqClient, LLMError, Usage


class FakeResponse:
    def __init__(self, status: int, body: dict | None = None, headers: dict | None = None):
        self.status_code = status
        self._body = body or {}
        self.headers = headers or {}
        self.text = json.dumps(self._body)

    def json(self) -> dict:
        return self._body


class FakeSession:
    """Returns queued responses in order and records every call."""

    def __init__(self, responses: list[FakeResponse]):
        self.responses = list(responses)
        self.calls: list[dict] = []

    def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "json": json})
        return self.responses.pop(0)


def ok(content: str) -> FakeResponse:
    return FakeResponse(
        200,
        {
            "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 3},
        },
    )


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr("enterprise_rag.llm.time.sleep", lambda s: None)


def make_client(session, monkeypatch, key="gsk_test"):
    monkeypatch.setenv("GROQ_API_KEY", key)
    return GroqClient("test-model", tokens_per_minute=8000, session=session)


def test_retries_on_429_then_succeeds(monkeypatch):
    session = FakeSession([FakeResponse(429, headers={"retry-after": "0"}), ok('{"a": 1}')])
    data, usage = make_client(session, monkeypatch).complete_json("sys", "user")
    assert data == {"a": 1}
    assert isinstance(usage, Usage)
    assert (usage.prompt_tokens, usage.completion_tokens) == (12, 3)
    assert len(session.calls) == 2
    assert session.calls[0]["json"]["response_format"] == {"type": "json_object"}


def test_raises_llm_error_after_max_retries(monkeypatch):
    session = FakeSession([FakeResponse(503) for _ in range(5)])
    with pytest.raises(LLMError):
        make_client(session, monkeypatch).complete_text("sys", "user")
    assert len(session.calls) == 5


def test_key_loaded_from_env_not_logged(monkeypatch):
    session = FakeSession([ok("hello")])
    client = make_client(session, monkeypatch)
    text, _ = client.complete_text("sys", "user")
    assert text == "hello"
    assert session.calls[0]["headers"]["Authorization"] == "Bearer gsk_test"
    assert "gsk_test" not in repr(client)


def test_load_eval_config_defaults():
    cfg = load_eval_config()
    assert cfg.quote_match_threshold == 0.80
    assert cfg.judge_model == "openai/gpt-oss-120b"
