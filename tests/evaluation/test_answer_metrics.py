import pytest

from enterprise_rag.evaluation import (
    GroqJudge,
    NumericAnswer,
    citation_precision,
    numeric_match,
    parse_numbers,
)
from enterprise_rag.llm import Usage
from enterprise_rag.retrieval import PipelineResponse, RetrievedChunk

USAGE = Usage(1, 1, 1.0)


class FakeClient:
    model = "judge-model"

    def __init__(self, json_replies=(), text="judged"):
        self.json_replies = list(json_replies)
        self.text = text

    def complete_text(self, system, user, temperature=0.0):
        return self.text, USAGE

    def complete_json(self, system, user, temperature=0.0):
        return self.json_replies.pop(0), USAGE


def test_parse_number_scales_and_negatives():
    assert 955_200_000 in [pytest.approx(n) for n in parse_numbers("$955.2 million")]
    assert parse_numbers("955,224") == [955_224]
    assert parse_numbers("(1,234)") == [-1234]
    assert parse_numbers("12.5%") == [12.5]
    assert parse_numbers("$1.2B and 40k") == [pytest.approx(1.2e9), 40_000]


def test_numeric_match_across_scales(make_item):
    item = make_item(numeric_answer=NumericAnswer(955224, "USD", 1000))
    assert numeric_match(item, "Revenue was $955.2 million.", 0.005)
    assert numeric_match(item, "It was 955,224 thousand.", 0.005)
    assert numeric_match(item, "955,224 (in thousands)", 0.005)
    assert not numeric_match(item, "Revenue was $950 million.", 0.005)


def test_groq_judge_uses_client():
    judge = GroqJudge(FakeClient(text="judged"))
    assert judge.generate("prompt") == "judged"
    assert judge.get_model_name() == "judge-model"


def test_citation_precision_counts_supported(make_item):
    chunks = (RetrievedChunk("a", "a#1", "text one", 1.0), RetrievedChunk("b", "b#1", "two", 1.0))
    resp = PipelineResponse("answer", False, ("a#1", "b#1"), chunks, None)
    client = FakeClient(json_replies=[{"supported": True}, {"supported": False}])
    assert citation_precision(make_item(), resp, client) == 0.5


def test_citation_precision_refused_without_citations(make_item):
    resp = PipelineResponse("", True, (), (), None)
    assert citation_precision(make_item(), resp, FakeClient()) == 1.0
