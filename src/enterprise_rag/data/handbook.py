"""Fetch the pinned handbook commit and copy the sampled pages into the raw corpus."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from enterprise_rag.config import DataConfig
from enterprise_rag.data.handbook_pages import eligible_pages, page_url, sample_pages
from enterprise_rag.data.manifest import DocumentRecord, allowed_roles_for, sha256_file

log = logging.getLogger(__name__)

SOURCE = "handbook"


def _git(repo_dir: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_dir), *args], check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def checkout_handbook(cfg: DataConfig) -> Path:
    """Shallow, blobless, sparse checkout of only the configured folders at the pinned commit.

    The full repo is several GB of history and images; this downloads only the markdown we sample.
    """
    hb = cfg.handbook
    repo_dir = cfg.cache_dir / "handbook"
    if not (repo_dir / ".git").exists():
        repo_dir.mkdir(parents=True, exist_ok=True)
        _git(repo_dir, "init", "-q")
        _git(repo_dir, "remote", "add", "origin", hb.repo)
    folders = sorted({f for s in hb.sections for f in s.folders})
    _git(repo_dir, "sparse-checkout", "set", "--no-cone",
         *[f"/{hb.content_root}/{f}/**/*.md" for f in folders])
    try:
        current = _git(repo_dir, "rev-parse", "HEAD")
    except subprocess.CalledProcessError:
        current = ""
    if current != hb.commit:
        log.info("Fetching handbook @ %s", hb.commit[:8])
        _git(repo_dir, "fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", hb.commit)
    _git(repo_dir, "checkout", "-q", "--detach", hb.commit)
    return repo_dir / hb.content_root


def fetch_handbook(cfg: DataConfig) -> list[DocumentRecord]:
    """Sample each section and copy its pages to raw_dir/handbook/, mirroring handbook paths."""
    content_root = checkout_handbook(cfg)
    out_root = cfg.raw_dir / SOURCE
    if out_root.exists():
        shutil.rmtree(out_root)  # a re-run must not leave pages from an older sample behind

    records = []
    for section in cfg.handbook.sections:
        pool = eligible_pages(content_root, section.folders, cfg.handbook.min_words)
        chosen = sample_pages(pool, section.pages, cfg.seed, section.name)
        log.info("handbook/%s: %d of %d eligible pages", section.name, len(chosen), len(pool))
        for page in chosen:
            dest = out_root / page.rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(content_root / page.rel_path, dest)
            records.append(
                DocumentRecord(
                    doc_id=f"{SOURCE}:{page.rel_path.removesuffix('.md')}",
                    source=SOURCE,
                    path=dest.relative_to(cfg.raw_dir).as_posix(),
                    title=page.title,
                    source_url=page_url(page.rel_path),
                    department=section.name,
                    allowed_roles=allowed_roles_for(section.role, cfg),
                    license=cfg.handbook.license,
                    content_hash=sha256_file(dest),
                )
            )
    return records
