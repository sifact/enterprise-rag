"""Typed view of configs/data_sources.yaml.

All corpus decisions (pins, sample sizes, role mapping) live in that one YAML file;
this module only parses and validates it so the rest of the code never reads raw dicts.
"""

from __future__ import annotations

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
