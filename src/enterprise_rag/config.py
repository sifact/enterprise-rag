"""Typed view of configs/data_sources.yaml.

All corpus decisions (pins, sample sizes, role mapping) live in that one YAML file;
this module only parses and validates it so the rest of the code never reads raw dicts.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "data_sources.yaml"


@dataclass(frozen=True)
class HandbookSection:
    """A group of handbook folders sampled together. `role=None` means visible to every role."""

    name: str
    folders: tuple[str, ...]
    pages: int
    role: str | None


@dataclass(frozen=True)
class HandbookConfig:
    repo: str
    commit: str
    content_root: str
    license: str
    min_words: int
    sections: tuple[HandbookSection, ...]


@dataclass(frozen=True)
class SecFiling:
    form: str
    period_end: str
    filed: str
    accession: str
    document: str


@dataclass(frozen=True)
class SecConfig:
    cik: int
    user_agent_env: str
    role: str
    filings: tuple[SecFiling, ...]


@dataclass(frozen=True)
class SyntheticFile:
    name: str
    contents: str


@dataclass(frozen=True)
class SyntheticConfig:
    role: str
    files: tuple[SyntheticFile, ...]


@dataclass(frozen=True)
class DataConfig:
    seed: int
    roles: tuple[str, ...]
    superuser_role: str
    raw_dir: Path
    cache_dir: Path
    handbook: HandbookConfig
    sec: SecConfig
    synthetic: SyntheticConfig

    @property
    def manifest_path(self) -> Path:
        return self.raw_dir / "manifest.jsonl"


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> DataConfig:
    """Parse the YAML and fail fast on role names that aren't declared in `roles`."""
    raw = yaml.safe_load(path.read_text())
    roles = tuple(raw["roles"])

    hb = raw["handbook"]
    sections = [
        HandbookSection(name, tuple(s["folders"]), int(s["pages"]), role=name)
        for name, s in hb["departments"].items()
    ]
    sections.append(
        HandbookSection("general", tuple(hb["general"]["folders"]), int(hb["general"]["pages"]), None)
    )

    sec = raw["sec_filings"]
    syn = raw["synthetic_xlsx"]
    cfg = DataConfig(
        seed=int(raw["seed"]),
        roles=roles,
        superuser_role=raw["superuser_role"],
        raw_dir=_resolve(raw["paths"]["raw_dir"]),
        cache_dir=_resolve(raw["paths"]["cache_dir"]),
        handbook=HandbookConfig(
            repo=hb["repo"],
            commit=hb["commit"],
            content_root=hb["content_root"],
            license=hb["license"],
            min_words=int(hb["min_words"]),
            sections=tuple(sections),
        ),
        sec=SecConfig(
            cik=int(sec["cik"]),
            user_agent_env=sec["user_agent_env"],
            role=sec["role"],
            filings=tuple(
                SecFiling(
                    form=f["form"],
                    period_end=str(f["period_end"]),
                    filed=str(f["filed"]),
                    accession=f["accession"],
                    document=f["document"],
                )
                for f in sec["filings"]
            ),
        ),
        synthetic=SyntheticConfig(
            role=syn["role"],
            files=tuple(SyntheticFile(f["name"], f["contents"]) for f in syn["files"]),
        ),
    )
    _validate_roles(cfg)
    return cfg


def _validate_roles(cfg: DataConfig) -> None:
    used = {s.role for s in cfg.handbook.sections if s.role} | {cfg.sec.role, cfg.synthetic.role}
    used.add(cfg.superuser_role)
    unknown = used - set(cfg.roles)
    if unknown:
        raise ValueError(f"Roles used in config but not declared in `roles`: {sorted(unknown)}")


DEFAULT_EVAL_CONFIG_PATH = PROJECT_ROOT / "configs" / "eval.yaml"


@dataclass(frozen=True)
class EvalConfig:
    """Typed view of configs/eval.yaml: models, thresholds and paths for the golden set."""

    seed: int
    drafting_model: str
    judge_model: str
    generator_model: str
    quote_match_threshold: float
    numeric_tolerance: float
    top_k: int
    golden_path: Path
    fixtures_dir: Path
    runs_dir: Path
    tokens_per_minute: int
    model_prices_usd_per_mtok: dict[str, tuple[float, float]]


def load_eval_config(path: Path = DEFAULT_EVAL_CONFIG_PATH) -> EvalConfig:
    raw = yaml.safe_load(path.read_text())
    prices = raw.get("model_prices_usd_per_mtok") or {}
    return EvalConfig(
        seed=int(raw["seed"]),
        drafting_model=raw["models"]["drafting"],
        judge_model=raw["models"]["judge"],
        generator_model=raw["models"]["generator"],
        quote_match_threshold=float(raw["quote_match_threshold"]),
        numeric_tolerance=float(raw["numeric_tolerance"]),
        top_k=int(raw["top_k"]),
        golden_path=_resolve(raw["paths"]["golden"]),
        fixtures_dir=_resolve(raw["paths"]["fixtures"]),
        runs_dir=_resolve(raw["paths"]["runs"]),
        tokens_per_minute=int(raw["tokens_per_minute"]),
        model_prices_usd_per_mtok={m: (float(p[0]), float(p[1])) for m, p in prices.items()},
    )


DEFAULT_RAG_CONFIG_PATH = PROJECT_ROOT / "configs" / "rag.yaml"


@dataclass(frozen=True)
class RagConfig:
    """Typed view of configs/rag.yaml: chunking, index, models, retrieval, guards and limits."""

    chunk_words: int
    chunk_overlap_words: int
    min_chunk_words: int
    sheet_rows_per_chunk: int
    sheet_overlap_rows: int
    index_dir: Path
    collection: str
    models_cache_dir: Path
    embed_model: str
    sparse_model: str
    rerank_model: str
    guard_model: str
    generator_model: str
    prefetch_limit: int
    rerank_candidates: int
    context_chunks: int
    guard_threshold: float
    evidence_threshold: float
    max_question_chars: int
    rate_per_minute: int
    rate_per_day: int


def load_rag_config(path: Path = DEFAULT_RAG_CONFIG_PATH) -> RagConfig:
    raw = yaml.safe_load(path.read_text())
    ch, ix, m = raw["chunking"], raw["index"], raw["models"]
    rt, gd, lm = raw["retrieval"], raw["guardrails"], raw["limits"]
    return RagConfig(
        chunk_words=int(ch["chunk_words"]),
        chunk_overlap_words=int(ch["chunk_overlap_words"]),
        min_chunk_words=int(ch["min_chunk_words"]),
        sheet_rows_per_chunk=int(ch["sheet_rows_per_chunk"]),
        sheet_overlap_rows=int(ch["sheet_overlap_rows"]),
        # RAG_INDEX_DIR lets a second process (the demo server, a container) use its own copy.
        index_dir=_resolve(os.environ.get("RAG_INDEX_DIR", ix["dir"])),
        collection=ix["collection"],
        models_cache_dir=_resolve(ix["models_cache_dir"]),
        embed_model=m["embed"],
        sparse_model=m["sparse"],
        rerank_model=m["rerank"],
        guard_model=m["guard"],
        generator_model=m["generator"],
        prefetch_limit=int(rt["prefetch_limit"]),
        rerank_candidates=int(rt["rerank_candidates"]),
        context_chunks=int(rt["context_chunks"]),
        guard_threshold=float(gd["guard_threshold"]),
        evidence_threshold=float(gd["evidence_threshold"]),
        max_question_chars=int(lm["max_question_chars"]),
        rate_per_minute=int(lm["rate_per_minute"]),
        rate_per_day=int(lm["rate_per_day"]),
    )
