"""Command-line entry point: `enterprise-rag fetch-data [--only SOURCE] [--force]`."""

from __future__ import annotations

import argparse
import logging
from collections import Counter
from pathlib import Path

from enterprise_rag.config import DEFAULT_CONFIG_PATH, load_config
from enterprise_rag.data import (
    FetchError,
    fetch_handbook,
    fetch_sec,
    fetch_synthetic,
    read_manifest,
    write_manifest,
)

SOURCES = ("handbook", "sec", "synthetic")
log = logging.getLogger("enterprise_rag")


def _fetch_data(args: argparse.Namespace) -> None:
    cfg = load_config(args.config)
    fetchers = {
        "handbook": lambda: fetch_handbook(cfg),
        "sec": lambda: fetch_sec(cfg, force=args.force),
        "synthetic": lambda: fetch_synthetic(cfg),
    }
    failed = []
    for source in [args.only] if args.only else SOURCES:
        # Write the manifest per source, so one failing source doesn't discard the others.
        try:
            write_manifest(cfg.manifest_path, fetchers[source](), replace_sources={source})
        except FetchError as exc:
            log.error("%s: %s", source, exc)
            failed.append(source)

    manifest = read_manifest(cfg.manifest_path)
    print(f"{len(manifest)} documents in {cfg.manifest_path}")
    for dept, n in sorted(Counter(r.department for r in manifest).items()):
        print(f"  {dept:<12} {n}")
    if failed:
        raise SystemExit(f"Failed sources: {', '.join(failed)}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="enterprise-rag")
    parser.add_argument("--config", type=Path,
                        default=DEFAULT_CONFIG_PATH)
    sub = parser.add_subparsers(dest="command", required=True)
    fetch = sub.add_parser("fetch-data", help="Download/generate the raw corpus and its manifest")
    fetch.add_argument("--only", choices=SOURCES, help="Refresh one source, keep the others")
    fetch.add_argument("--force", action="store_true", help="Re-download SEC filings")
    fetch.set_defaults(func=_fetch_data)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args.func(args)


if __name__ == "__main__":
    main()
