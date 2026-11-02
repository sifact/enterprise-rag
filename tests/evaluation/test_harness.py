import json
from dataclasses import replace

from enterprise_rag.config import load_eval_config
from enterprise_rag.evaluation import (
    load_run,
    render_ablation_table,
    run_eval,
    write_run,
)
from enterprise_rag.retrieval import PipelineResponse, RetrievedChunk

from .conftest import ENG_TEXT


class FakePipeline:
    """Returns the engineering page for every question, whoever asks."""

    name = "fake"

    def retrieve(self, question, role, k):
        return [RetrievedChunk("handbook:eng", "handbook:eng#0", ENG_TEXT, 1.0)][:k]

    def answer(self, question, role):
        refused = "refuse" in question
        return PipelineResponse("" if refused else "One maintainer approval.", refused, (),
                                tuple(self.retrieve(question, role, 10)), None)


def items(make_item):
    answer = make_item(id="a1", split="test")
    refuse = make_item(id="r1", category="out_of_scope", expected_behavior="refuse",
                       question="please refuse", reference_answer="", gold_evidence=(),
                       asked_as="engineering", split="test")
    cross = make_item(id="x1", category="cross_role", expected_behavior="refuse",
                      question="please refuse", reference_answer="", gold_evidence=(),
                      asked_as="legal", forbidden_doc_ids=("handbook:eng",), split="test")
    return [answer, refuse, cross]


def run(make_item, manifest, tmp_path, retrieval_only=False):
    cfg = replace(load_eval_config(), runs_dir=tmp_path)
    return run_eval(FakePipeline(), items(make_item), cfg, manifest, judge=None,
                    retrieval_only=retrieval_only, split="test")


def test_aggregates_only_answer_items_for_retrieval_metrics(make_item, manifest, tmp_path):
    result = run(make_item, manifest, tmp_path, retrieval_only=True)
    assert result.aggregates["hit@5"] == 1.0
    assert result.aggregates["n_retrieval_items"] == 1


def test_leak_rate_counts_cross_role_items(make_item, manifest, tmp_path):
    result = run(make_item, manifest, tmp_path)
    by_id = {r.id: r for r in result.items}
    assert by_id["x1"].metrics["retrieval_leak"] is True
    assert by_id["a1"].metrics["retrieval_leak"] is False
    assert result.aggregates["leak_rate"] == 1 / 3
    assert result.aggregates["refusal_accuracy"] == 1.0
    assert result.aggregates["false_refusal_rate"] == 0.0


def test_run_file_round_trip_and_no_secrets(make_item, manifest, tmp_path, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_secret")
    result = run(make_item, manifest, tmp_path)
    path = write_run(result, tmp_path)
    assert load_run(path) == result
    text = path.read_text()
    assert "gsk_secret" not in text
    assert ENG_TEXT[:40] not in text  # chunk text is never stored
    assert json.loads(text)["pipeline_name"] == "fake"


def test_render_ablation_table_has_header_and_dash_for_missing(make_item, manifest, tmp_path):
    path = write_run(run(make_item, manifest, tmp_path, retrieval_only=True), tmp_path)
    table = render_ablation_table([path])
    lines = table.splitlines()
    assert lines[0].startswith("| Run | Config | hit@5 | MRR@10 | nDCG@10 | Faithfulness |")
    assert "| — |" in lines[2]  # no faithfulness in a retrieval-only run


class AlwaysRefuses(FakePipeline):
    def answer(self, question, role):
        return PipelineResponse("", True, (), tuple(self.retrieve(question, role, 10)), None)


def test_refusal_accuracy_counts_only_refuse_items(make_item, manifest, tmp_path):
    cfg = replace(load_eval_config(), runs_dir=tmp_path)
    result = run_eval(AlwaysRefuses(), items(make_item), cfg, manifest, judge=None,
                      retrieval_only=False, split="test")
    assert result.aggregates["refusal_accuracy"] == 1.0  # both refuse items were refused
    assert result.aggregates["false_refusal_rate"] == 1.0  # the answer item was refused


class Flaky(FakePipeline):
    def answer(self, question, role):
        from enterprise_rag.llm import LLMError

        raise LLMError("groq down")


def test_llm_error_on_one_item_is_recorded_not_fatal(make_item, manifest, tmp_path):
    cfg = replace(load_eval_config(), runs_dir=tmp_path)
    result = run_eval(Flaky(), items(make_item), cfg, manifest, judge=None,
                      retrieval_only=False, split="test")
    assert len(result.items) == 3
    assert all(r.error and "groq down" in r.error for r in result.items)
    assert result.aggregates["n_errors"] == 3
