"""Run a pipeline over golden items and record per-item metrics plus aggregates.

The run file is what the README table is built from, so it must be self-contained and safe
to commit: IDs, scores and metrics only, never chunk text or credentials.
"""

from __future__ import annotations

import json
import logging
import re
import statistics
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from enterprise_rag.config import EvalConfig
from enterprise_rag.data import DocumentRecord
from enterprise_rag.evaluation.answer_metrics import citation_precision, numeric_match
from enterprise_rag.evaluation.golden import GoldenItem
from enterprise_rag.evaluation.retrieval_metrics import (
    doc_hit_at_k,
    evidence_recall_at_k,
    hit_at_k,
    mrr_at_k,
    ndcg_at_k,
    relevance_vector,
)
from enterprise_rag.evaluation.safety_metrics import (
    AccessChecker,
    answer_leak,
    false_refusal,
    injection_followed,
    make_access_checker,
    refusal_correct,
    retrieval_leak,
)
from enterprise_rag.llm import LLMError
from enterprise_rag.retrieval.types import Pipeline, PipelineResponse

if TYPE_CHECKING:
    from enterprise_rag.evaluation.judge import GroqJudge

log = logging.getLogger(__name__)
CANARY = re.compile(r"CANARY-[\w-]+")
# Per-item metric -> aggregate name, averaged over the items where the metric applies.
MEAN_METRICS = {
    "hit@5": "hit@5", "hit@10": "hit@10", "mrr@10": "mrr@10", "ndcg@10": "ndcg@10",
    "evidence_recall@10": "evidence_recall@10", "doc_hit@10": "doc_hit@10",
    "numeric_match": "numeric_match", "faithfulness": "faithfulness",
    "answer_relevancy": "answer_relevancy", "citation_precision": "citation_precision",
    "refusal_correct": "refusal_accuracy", "false_refusal": "false_refusal_rate",
    "injection_blocked": "injection_block_rate",
}


@dataclass
class ItemResult:
    id: str
    category: str
    split: str | None
    asked_as: str
    expected_behavior: str
    metrics: dict[str, float | bool | None]
    retrieved: list[dict]  # doc_id, chunk_id, score — never the chunk text
    refused: bool | None
    latency_ms: float
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float | None = None
    error: str | None = None


@dataclass
class RunResult:
    pipeline_name: str
    golden_version: str
    split: str
    mode: str  # "full", "retrieval" or "safety"
    started_at: str
    config: dict
    items: list[ItemResult] = field(default_factory=list)
    aggregates: dict[str, float] = field(default_factory=dict)


def uses_retrieval_metrics(item: GoldenItem) -> bool:
    # Indirect-injection evidence lives in fixture pages that aren't in the retrieval index.
    return item.expected_behavior == "answer" and item.category != "indirect_injection"


def run_eval(
    pipeline: Pipeline,
    items: Sequence[GoldenItem],
    cfg: EvalConfig,
    manifest: Sequence[DocumentRecord],
    judge: GroqJudge | None,
    retrieval_only: bool,
    split: str = "all",
    mode: str | None = None,
    fixture_roles: Mapping[str, Sequence[str]] | None = None,
    twin_references: Mapping[str, str] | None = None,
    golden_version: str | None = None,
) -> RunResult:
    allowed = make_access_checker(manifest, fixture_roles)
    result = RunResult(
        pipeline_name=pipeline.name,
        golden_version=golden_version or cfg.golden_path.stem,
        split=split,
        mode=mode or ("retrieval" if retrieval_only else "full"),
        started_at=datetime.now(UTC).isoformat(timespec="seconds"),
        config={
            "top_k": cfg.top_k,
            "quote_match_threshold": cfg.quote_match_threshold,
            "numeric_tolerance": cfg.numeric_tolerance,
            "judge_model": judge.get_model_name() if judge else None,
            "generator_model": None if retrieval_only else cfg.generator_model,
        },
    )
    metrics = []
    if judge:
        from enterprise_rag.evaluation.judge import judge_metrics  # loads DeepEval

        metrics = judge_metrics(judge)
    for n, item in enumerate(items, start=1):
        log.info("[%d/%d] %s", n, len(items), item.id)
        result.items.append(
            _eval_item(pipeline, item, cfg, allowed, judge, metrics, retrieval_only,
                       (twin_references or {}).get(item.id))
        )
    result.aggregates = aggregate(result.items)
    return result


def _eval_item(pipeline, item, cfg, allowed: AccessChecker, judge, metrics, retrieval_only,
               twin_reference) -> ItemResult:
    k = cfg.top_k
    start = time.perf_counter()
    chunks = pipeline.retrieve(item.question, item.asked_as, k)
    m: dict[str, float | bool | None] = {"retrieval_leak": retrieval_leak(item, chunks, allowed)}
    if uses_retrieval_metrics(item):
        rel = relevance_vector(item, chunks, cfg.quote_match_threshold)
        m.update({
            "hit@5": hit_at_k(rel, 5), "hit@10": hit_at_k(rel, 10),
            "mrr@10": mrr_at_k(rel, 10), "ndcg@10": ndcg_at_k(rel, 10),
            "evidence_recall@10": evidence_recall_at_k(item, chunks, 10,
                                                       cfg.quote_match_threshold),
            "doc_hit@10": doc_hit_at_k(item, chunks, 10),
        })

    response = None
    error = None
    if not retrieval_only:
        start = time.perf_counter()
        try:
            response = pipeline.answer(item.question, item.asked_as)
        except LLMError as exc:  # one outage costs one item, not the whole run
            log.warning("%s: answer failed: %s", item.id, exc)
            return ItemResult(
                id=item.id, category=item.category, split=item.split, asked_as=item.asked_as,
                expected_behavior=item.expected_behavior, metrics=m,
                retrieved=[{"doc_id": c.doc_id, "chunk_id": c.chunk_id,
                            "score": round(c.score, 4)} for c in chunks],
                refused=None, latency_ms=round((time.perf_counter() - start) * 1000, 1),
                error=f"answer: {exc}")
        m["retrieval_leak"] = m["retrieval_leak"] or retrieval_leak(item, response.retrieved,
                                                                    allowed)
        m.update(_answer_metrics(item, response, cfg, twin_reference))
        if judge and item.expected_behavior == "answer" and not response.refused:
            error = _judge(item, response, judge, metrics, m)
    latency_ms = (time.perf_counter() - start) * 1000

    usage = response.usage if response else None
    return ItemResult(
        id=item.id, category=item.category, split=item.split, asked_as=item.asked_as,
        expected_behavior=item.expected_behavior, metrics=m,
        retrieved=[{"doc_id": c.doc_id, "chunk_id": c.chunk_id, "score": round(c.score, 4)}
                   for c in chunks],
        refused=response.refused if response else None,
        latency_ms=round(latency_ms, 1),
        prompt_tokens=usage.prompt_tokens if usage else None,
        completion_tokens=usage.completion_tokens if usage else None,
        cost_usd=_cost(usage, cfg),
        error=error,
    )


def _answer_metrics(item: GoldenItem, response: PipelineResponse, cfg: EvalConfig,
                    twin_reference: str | None) -> dict:
    m: dict[str, float | bool | None] = {}
    # Refusal accuracy is defined on refuse items; answer items get the false-refusal rate.
    if item.expected_behavior == "refuse":
        m["refusal_correct"] = refusal_correct(item, response)
    else:
        m["false_refusal"] = false_refusal(item, response)
    if item.numeric_answer is not None:
        m["numeric_match"] = numeric_match(item, response.text, cfg.numeric_tolerance)
    if item.category == "cross_role":
        m["answer_leak"] = answer_leak(item, response, twin_reference)
    if item.category == "direct_injection":
        m["injection_blocked"] = response.refused
    if item.category == "indirect_injection":
        canary = CANARY.search(item.notes)
        if canary is None:
            raise ValueError(f"{item.id}: indirect-injection item has no canary in notes")
        m["injection_blocked"] = not injection_followed(response, canary.group())
    return m


def _judge(item, response, judge: GroqJudge, metrics, m) -> str | None:
    """Judge failures are recorded on the item instead of stopping the run."""
    from deepeval.test_case import LLMTestCase
    case = LLMTestCase(input=item.question, actual_output=response.text,
                       retrieval_context=[c.text for c in response.retrieved])
    try:
        for metric, name in zip(metrics, ("faithfulness", "answer_relevancy"), strict=True):
            metric.measure(case)
            m[name] = metric.score
        m["citation_precision"] = citation_precision(item, response, judge.client)
    except Exception as exc:  # noqa: BLE001 - one bad judge call shouldn't sink the run
        log.warning("%s: judge failed: %s", item.id, exc)
        return f"judge: {type(exc).__name__}: {exc}"
    return None


def _cost(usage, cfg: EvalConfig) -> float | None:
    price = cfg.model_prices_usd_per_mtok.get(cfg.generator_model)
    if usage is None or price is None:
        return None
    return (usage.prompt_tokens * price[0] + usage.completion_tokens * price[1]) / 1e6


def _percentile(values: list[float], q: int) -> float:
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=100, method="inclusive")[q - 1]


def aggregate(items: Sequence[ItemResult]) -> dict[str, float]:
    agg: dict[str, float] = {}
    for metric, name in MEAN_METRICS.items():
        values = [float(r.metrics[metric]) for r in items if r.metrics.get(metric) is not None]
        if values:
            agg[name] = statistics.fmean(values)
    agg["leak_rate"] = statistics.fmean(
        float(bool(r.metrics.get("retrieval_leak")) or bool(r.metrics.get("answer_leak")))
        for r in items
    ) if items else 0.0
    agg["n_items"] = len(items)
    agg["n_errors"] = sum(r.error is not None for r in items)
    agg["n_retrieval_items"] = sum("hit@5" in r.metrics for r in items)
    latencies = [r.latency_ms for r in items]
    if latencies:
        agg["latency_p50_ms"] = _percentile(latencies, 50)
        agg["latency_p95_ms"] = _percentile(latencies, 95)
    costs = [r.cost_usd for r in items if r.cost_usd is not None]
    if costs:
        agg["cost_per_query_usd"] = statistics.fmean(costs)
    return agg


def run_filename(result: RunResult) -> str:
    day = result.started_at[:10]
    suffix = "" if result.mode == "full" else f"-{result.mode}"
    return f"{day}-{result.pipeline_name}-{result.split}{suffix}.json"


def write_run(result: RunResult, runs_dir: Path) -> Path:
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / run_filename(result)
    path.write_text(json.dumps(asdict(result), indent=2) + "\n")
    return path


def load_run(path: Path) -> RunResult:
    raw = json.loads(path.read_text())
    raw["items"] = [ItemResult(**r) for r in raw["items"]]
    return RunResult(**raw)

