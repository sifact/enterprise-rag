"""Command-line entry point.

- `enterprise-rag fetch-data [--only SOURCE] [--force]`: build the raw corpus.
- `enterprise-rag eval --pipeline NAME --split SPLIT [--retrieval-only | --safety-only]`.
- `enterprise-rag report RUN.json...`: print the ablation table.
- `enterprise-rag draft-golden`: LLM-draft answerable items for review.
- `enterprise-rag build-golden [--spot-check]`: merge reviewed items and freeze the set.
- `enterprise-rag build-index [--with-fixtures]`: chunk the corpus and build the search index.
- `enterprise-rag serve [--host] [--port]`: run the web app (API + built UI).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
from collections import Counter
from dataclasses import replace
from pathlib import Path

from enterprise_rag.config import (
    DEFAULT_CONFIG_PATH,
    PROJECT_ROOT,
    load_config,
    load_eval_config,
    load_rag_config,
)
from enterprise_rag.data import (
    FetchError,
    fetch_handbook,
    fetch_sec,
    fetch_synthetic,
    load_doc_pages,
    load_fixture_pages,
    load_fixture_roles,
    read_manifest,
    write_manifest,
)
from enterprise_rag.evaluation import (
    CATEGORIES,
    DraftPlan,
    GroqJudge,
    assemble,
    computed_items,
    draft_all,
    load_golden,
    load_handwritten,
    parse_review_decisions,
    render_ablation_table,
    reviewed_drafts,
    run_eval,
    sample_passages,
    save_golden,
    spot_check_ids,
    write_review_file,
    write_run,
)
from enterprise_rag.indexing import FastEmbedders, build_index, chunk_corpus, open_client
from enterprise_rag.llm import GroqClient
from enterprise_rag.pipeline import PIPELINE_NAMES, build_pipeline, build_rag, collection_name

SOURCES = ("handbook", "sec", "synthetic")
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
    pipeline = build_pipeline(args.pipeline, data_cfg, load_rag_config(), cfg,
                              safety=args.safety_only)
    judge = None
    if not (args.retrieval_only or args.safety_only or args.no_judge):
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


def _draft_golden(args: argparse.Namespace) -> None:
    data_cfg = load_config(args.config)
    cfg = load_eval_config()
    review_dir = cfg.golden_path.parent / "review"
    drafts_path = review_dir / f"{cfg.golden_path.stem}_drafts.jsonl"
    seed = cfg.seed if args.seed is None else args.seed

    existing = load_golden(drafts_path) if args.top_up else []
    plan = DraftPlan(oversample=args.oversample)
    quotas = plan.quotas()
    if args.top_up:
        # e.g. multi_hop=5: draft only these buckets, appended to the reviewed drafts.
        quotas = {b: int(n) for b, n in (pair.split("=") for pair in args.top_up)}
    manifest = read_manifest(data_cfg.manifest_path)
    passages = [p for p in sample_passages(plan, manifest, data_cfg.raw_dir, seed)
                if p.bucket in quotas]
    log.info("Sampled %d passages for %d buckets (seed %d)", len(passages), len(quotas), seed)
    client = GroqClient(cfg.drafting_model, cfg.tokens_per_minute)
    new = draft_all(passages, client, quotas, {i.question for i in existing})

    taken = {i.id for i in existing}
    new = [i if i.id not in taken else replace(i, id=f"{i.id}-s{seed}") for i in new]
    items = existing + new
    save_golden(drafts_path, items)
    write_review_file(new, review_dir / f"{cfg.golden_path.stem}_review.md",
                      append=bool(args.top_up))
    print(f"{len(new)} new drafts; {len(items)} in {drafts_path}")
    for cat, n in sorted(Counter(i.category for i in new).items()):
        print(f"  {cat:<14} {n}")


def _build_index(args: argparse.Namespace) -> None:
    data_cfg, rag = load_config(args.config), load_rag_config()
    fixtures = load_eval_config().fixtures_dir if args.with_fixtures else None
    collection = collection_name(rag, safety=args.with_fixtures)
    chunks = chunk_corpus(read_manifest(data_cfg.manifest_path), data_cfg.raw_dir, rag, fixtures)
    n = build_index(chunks, FastEmbedders(rag), open_client(rag), collection)
    print(f"Indexed {n} chunks into {collection} at {rag.index_dir}")


SPOT_CHECK_HEADING = "# User spot-check"


def _build_golden(args: argparse.Namespace) -> None:
    data_cfg = load_config(args.config)
    cfg = load_eval_config()
    golden_dir = cfg.golden_path.parent
    stem = cfg.golden_path.stem
    review_path = golden_dir / "review" / f"{stem}_review.md"
    drafts = reviewed_drafts(load_golden(golden_dir / "review" / f"{stem}_drafts.jsonl"),
                             parse_review_decisions(review_path))
    handwritten = load_handwritten(golden_dir / "handwritten.yaml")
    manifest = read_manifest(data_cfg.manifest_path)
    doc_texts = {r.doc_id: load_doc_pages(r, data_cfg.raw_dir) for r in manifest}
    doc_texts |= load_fixture_pages(cfg.fixtures_dir)
    items = assemble(drafts, computed_items(data_cfg), handwritten, manifest, doc_texts,
                     data_cfg.roles, data_cfg.superuser_role, cfg.seed)
    for cat, n in sorted(Counter(i.category for i in items).items()):
        print(f"  {cat:<22} {n}")
    print(f"  total {len(items)}; " + ", ".join(
        f"{s} {n}" for s, n in sorted(Counter(i.split for i in items).items())))

    if args.spot_check:
        _write_spot_check(review_path, [i for i in items if i.id in
                                        set(spot_check_ids(items, cfg.seed))])
        return
    if cfg.golden_path.exists() and not args.force:
        raise SystemExit(f"{cfg.golden_path} is frozen; bump the version instead of overwriting")
    save_golden(cfg.golden_path, items)
    print(f"Wrote {cfg.golden_path}")


def _write_spot_check(review_path: Path, items) -> None:
    """Replace the spot-check section at the end of the review file."""
    text = review_path.read_text().split("\n" + SPOT_CHECK_HEADING)[0].rstrip()
    lines = ["", "", SPOT_CHECK_HEADING, "",
             (f"{len(items)} items sampled at random (seed from configs/eval.yaml) from every "
              "source. Note any change under the item; edits are recorded in `notes`."), ""]
    for i in items:
        lines += [f"### {i.id} ({i.category}, asked as `{i.asked_as}`, {i.expected_behavior})",
                  "", f"- Question: {i.question}"]
        if i.reference_answer:
            lines.append(f"- Answer: {i.reference_answer}")
        lines += [f"- Evidence `{e.doc_id}`{f' p{e.page}' if e.page else ''}: "
                  f"\"{' '.join(e.quote.split())}\"" for e in i.gold_evidence]
        if i.forbidden_doc_ids:
            lines.append(f"- Must not see: {', '.join(i.forbidden_doc_ids)}")
        lines += [f"- Notes: {i.notes}", "", "User comment:", ""]
    review_path.write_text(text + "\n".join(lines))
    print(f"Spot-check list ({len(items)} items) added to {review_path}")


def _serve(args: argparse.Namespace) -> None:
    import uvicorn

    from enterprise_rag.serving import build_meta, create_app

    data_cfg, rag, ev = load_config(args.config), load_rag_config(), load_eval_config()
    meta = build_meta(read_manifest(data_cfg.manifest_path), load_golden(ev.golden_path),
                      data_cfg.roles)
    # The demo searches the collection that includes the poisoned pages, so visitors can see
    # the injection defences work.
    pipeline = build_rag(rag, ev, safety=True)
    app = create_app(pipeline, rag, data_cfg.roles, meta, runs_dir=ev.runs_dir,
                     static_dir=PROJECT_ROOT / "web" / "dist",
                     secret=os.environ.get("SESSION_SECRET"))
    uvicorn.run(app, host=args.host, port=args.port, proxy_headers=True,
                forwarded_allow_ips="*")


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
    ev.add_argument("--pipeline", choices=PIPELINE_NAMES, required=True)
    ev.add_argument("--split", choices=("dev", "test", "all"), default="test")
    ev.add_argument("--golden", type=Path, help="Golden JSONL (default from configs/eval.yaml)")
    only = ev.add_mutually_exclusive_group()
    only.add_argument("--retrieval-only", action="store_true", help="Skip answers and the judge")
    only.add_argument("--safety-only", action="store_true",
                      help="Only refuse and injection items, with the poisoned fixtures indexed")
    ev.add_argument("--no-judge", action="store_true",
                    help="Skip the LLM-judge metrics (faithfulness, relevancy, citations)")
    ev.set_defaults(func=_eval)

    draft = sub.add_parser("draft-golden", help="LLM-draft answerable golden items for review")
    draft.add_argument("--top-up", nargs="+", metavar="BUCKET=N",
                       help="Only draft these buckets and append to the existing drafts")
    draft.add_argument("--seed", type=int, help="Sampling seed (default from configs/eval.yaml)")
    draft.add_argument("--oversample", type=float, default=1.5,
                       help="Passages sampled per needed item")
    draft.set_defaults(func=_draft_golden)

    build = sub.add_parser("build-golden", help="Merge reviewed items and freeze the golden set")
    build.add_argument("--spot-check", action="store_true",
                       help="Only list the user spot-check sample in the review file")
    build.add_argument("--force", action="store_true", help="Overwrite a frozen golden file")
    build.set_defaults(func=_build_golden)

    index = sub.add_parser("build-index", help="Chunk the corpus and build the search index")
    index.add_argument("--with-fixtures", action="store_true",
                       help="Also index the poisoned pages (separate collection, safety runs)")
    index.set_defaults(func=_build_index)

    serve = sub.add_parser("serve", help="Run the web app: API plus the built UI")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    serve.set_defaults(func=_serve)

    rep = sub.add_parser("report", help="Print the ablation table from run files")
    rep.add_argument("runs", type=Path, nargs="+")
    rep.set_defaults(func=_report)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args.func(args)


if __name__ == "__main__":
    main()
