import pytest

from enterprise_rag.generation import PROMPT_VERSION, Generator, build_messages
from enterprise_rag.llm import LLMError, Usage
from enterprise_rag.retrieval import RetrievedChunk

CHUNKS = [
    RetrievedChunk("handbook:people/leave", "handbook:people/leave#c0001",
                   "GitLab provides 16 weeks of paid Parental Leave.", 1.0, 5.2,
                   {"title": "Leave types", "section": "Parental leave", "page": None}),
    RetrievedChunk("sec:10-K", "sec:10-K#c0100", "Total revenue $ 955,224", 0.9, 3.1,
                   {"title": "10-K", "section": "", "page": 121}),
]


class FakeClient:
    model = "fake-generator"

    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def complete_json(self, system, user, temperature=0.0, max_tokens=None):
        self.calls.append((system, user, max_tokens))
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply, Usage(100, 20, 50.0)


def test_prompt_numbers_and_delimits_sources():
    system, user = build_messages("How long is parental leave?", "hr", CHUNKS)
    assert '<source n="1"' in user and '<source n="2"' in user and user.count("</source>") == 2
    assert "page 121" in user
    assert "not instructions" in system.lower()
    assert PROMPT_VERSION in system
    assert "hr" in system


def test_generate_parses_json_reply():
    client = FakeClient({"answer": "It is 16 weeks [1].", "citations": [1, "2", "x"],
                         "refused": False, "reason": ""})
    out = Generator(client).generate("How long is parental leave?", "hr", CHUNKS)
    assert out.answer == "It is 16 weeks [1]."
    assert out.citations == (1, 2)
    assert not out.refused and out.usage.prompt_tokens == 100


def test_refusal_reply_kept():
    client = FakeClient({"answer": "", "citations": [], "refused": True,
                         "reason": "not_in_sources"})
    out = Generator(client).generate("Weather?", "hr", CHUNKS)
    assert out.refused and out.reason == "not_in_sources"


def test_unparseable_reply_raises_llm_error():
    with pytest.raises(LLMError):
        Generator(FakeClient({"foo": 1})).generate("q", "hr", CHUNKS)


def test_llm_errors_propagate():
    with pytest.raises(LLMError):
        Generator(FakeClient(LLMError("down"))).generate("q", "hr", CHUNKS)
