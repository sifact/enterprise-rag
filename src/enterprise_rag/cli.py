"""Command-line entry point.

- `enterprise-rag fetch-data [--only SOURCE] [--force]`: build the raw corpus.
- `enterprise-rag eval --pipeline NAME --split SPLIT [--retrieval-only | --safety-only]`.
- `enterprise-rag report RUN.json...`: print the ablation table.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from collections import Counter
from pathlib import Path

from enterprise_rag.config import DEFAULT_CONFIG_PATH, load_config, load_eval_config
from enterprise_rag.data import (
    FetchError,
    fetch_handbook,
    fetch_sec,
    fetch_synthetic,
    load_fixture_roles,
    read_manifest,
    write_manifest,
)
from enterprise_rag.evaluation import (
    CATEGORIES,
    GroqJudge,
    load_golden,
    render_ablation_table,
    run_eval,
    write_run,
)
from enterprise_rag.llm import GroqClient
from enterprise_rag.retrieval import ReferenceBM25

SOURCES = ("handbook", "sec", "synthetic")
PIPELINES = {"reference-bm25": ReferenceBM25}
SAFETY_CATEGORIES = {c for c, b in CATEGORIES.items() if b == "refuse"} | {"indirect_injection"}
TWIN_NOTE = re.compile(r"twin: ([\w-]+)")
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


def _eval(args: argparse.Namespace) -> None:
    data_cfg = load_config(args.config)
    cfg = load_eval_config()
    golden_path = args.golden or cfg.golden_path
    golden = load_golden(golden_path)
    items = [i for i in golden if args.split == "all" or i.split == args.split]
    if args.safety_only:
        items = [i for i in items if i.category in SAFETY_CATEGORIES]
    else:
        # Indirect-injection pages are only indexed for safety runs.
        items = [i for i in items if i.category != "indirect_injection"]

    manifest = read_manifest(data_cfg.manifest_path)
    fixtures_dir = cfg.fixtures_dir if args.safety_only else None
    pipeline = PIPELINES[args.pipeline](manifest, data_cfg.raw_dir, fixtures_dir=fixtures_dir)
    judge = None
    if not (args.retrieval_only or args.safety_only):
        judge = GroqJudge(GroqClient(cfg.judge_model, cfg.tokens_per_minute))

    by_id = {i.id: i for i in golden}
    twins = {i.id: by_id[m.group(1)].reference_answer for i in golden
             if (m := TWIN_NOTE.search(i.notes)) and m.group(1) in by_id}
    mode = "retrieval" if args.retrieval_only else "safety" if args.safety_only else "full"
    result = run_eval(
        pipeline, items, cfg, manifest, judge, retrieval_only=args.retrieval_only,
        split=args.split, mode=mode,
        fixture_roles=load_fixture_roles(cfg.fixtures_dir) if args.safety_only else None,
        twin_references=twins, golden_version=golden_path.stem,
    )
    path = write_run(result, cfg.runs_dir)
    print(json.dumps(result.aggregates, indent=2))
    print(f"Run written to {path}")


def _report(args: argparse.Namespace) -> None:
    print(render_ablation_table(args.runs))


def main() -> None:
    parser = argparse.ArgumentParser(prog="enterprise-rag")
    parser.add_argument("--config", type=Path,
                        default=DEFAULT_CONFIG_PATH)
    sub = parser.add_subparsers(dest="command", required=True)
    fetch = sub.add_parser("fetch-data", help="Download/generate the raw corpus and its manifest")
    fetch.add_argument("--only", choices=SOURCES, help="Refresh one source, keep the others")
    fetch.add_argument("--force", action="store_true", help="Re-download SEC filings")
    fetch.set_defaults(func=_fetch_data)

    ev = sub.add_parser("eval", help="Score a pipeline on the golden set")
    ev.add_argument("--pipeline", choices=sorted(PIPELINES), required=True)
    ev.add_argument("--split", choices=("dev", "test", "all"), default="test")
    ev.add_argument("--golden", type=Path, help="Golden JSONL (default from configs/eval.yaml)")
    only = ev.add_mutually_exclusive_group()
    only.add_argument("--retrieval-only", action="store_true", help="Skip answers and the judge")
    only.add_argument("--safety-only", action="store_true",
                      help="Only refuse and injection items, with the poisoned fixtures indexed")
    ev.set_defaults(func=_eval)

    rep = sub.add_parser("report", help="Print the ablation table from run files")
    rep.add_argument("runs", type=Path, nargs="+")
    rep.set_defaults(func=_report)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args.func(args)


if __name__ == "__main__":
    main()
