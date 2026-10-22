"""Download GitLab's 10-K/10-Q from EDGAR and render each to PDF.

EDGAR publishes these filings as inline-XBRL HTML only. The project brief is about PDFs and
financial tables, so each filing is printed to PDF with headless Chromium; the HTML is kept
too, since it's the authoritative original.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import requests

from enterprise_rag.config import DataConfig, SecFiling
from enterprise_rag.data.manifest import DocumentRecord, allowed_roles_for, sha256_file

log = logging.getLogger(__name__)

SOURCE = "sec"
EDGAR_ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
REQUEST_INTERVAL_S = 0.2  # EDGAR's fair-access limit is 10 requests/second


class FetchError(RuntimeError):
    """A source couldn't be fetched for a reason the user has to fix (not a code bug)."""


def filing_url(cik: int, filing: SecFiling) -> str:
    return f"{EDGAR_ARCHIVES}/{cik}/{filing.accession.replace('-', '')}/{filing.document}"


def filing_stem(filing: SecFiling) -> str:
    return f"gitlab_{filing.form.lower().replace('-', '')}_{filing.period_end}"


def _user_agent(env_var: str) -> str:
    """EDGAR's fair-access policy requires a declared contact; it returns 403 without one."""
    ua = os.environ.get(env_var, "").strip()
    if "@" not in ua:
        raise FetchError(f"set {env_var} to 'Your Name your@email' (EDGAR requires a contact)")
    return ua


def download_filing(url: str, dest: Path, user_agent: str) -> None:
    resp = requests.get(url, headers={"User-Agent": user_agent}, timeout=60)
    if resp.status_code == 403:
        raise FetchError(f"EDGAR refused {url} (403); check the {user_agent!r} user agent")
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    time.sleep(REQUEST_INTERVAL_S)


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    """Print the filing to Letter-size PDF. Images (e.g. the logo) are relative links and are skipped."""
    from playwright.sync_api import sync_playwright  # heavy import, only needed here

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html_path.resolve().as_uri(), wait_until="load")
        page.pdf(path=str(pdf_path), format="Letter", print_background=True,
                 margin={"top": "0.5in", "bottom": "0.5in", "left": "0.5in", "right": "0.5in"})
        browser.close()


def fetch_sec(cfg: DataConfig, force: bool = False) -> list[DocumentRecord]:
    """Idempotent: existing files are reused unless `force`. The PDF is what gets ingested."""
    out_dir = cfg.raw_dir / SOURCE
    out_dir.mkdir(parents=True, exist_ok=True)
    user_agent = _user_agent(cfg.sec.user_agent_env)

    records = []
    for filing in cfg.sec.filings:
        url = filing_url(cfg.sec.cik, filing)
        stem = filing_stem(filing)
        html_path, pdf_path = out_dir / f"{stem}.htm", out_dir / f"{stem}.pdf"
        if force or not html_path.exists():
            log.info("Downloading %s", url)
            download_filing(url, html_path, user_agent)
        if force or not pdf_path.exists():
            log.info("Rendering %s", pdf_path.name)
            render_pdf(html_path, pdf_path)
        records.append(
            DocumentRecord(
                doc_id=f"{SOURCE}:{filing.form}:{filing.period_end}",
                source=SOURCE,
                path=pdf_path.relative_to(cfg.raw_dir).as_posix(),
                title=f"GitLab Inc. Form {filing.form} for period ending {filing.period_end}",
                source_url=url,
                department=cfg.sec.role,
                allowed_roles=allowed_roles_for(cfg.sec.role, cfg),
                license="public SEC filing",
                content_hash=sha256_file(pdf_path),
            )
        )
    return records
