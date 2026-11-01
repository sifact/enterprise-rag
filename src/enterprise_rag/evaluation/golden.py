"""Golden item schema, JSONL storage, the dev/test split and structural validation.

Gold labels are verbatim quotes, never chunk IDs, so any chunking setup can be scored
against the same file. Validation fails loudly with every bad item ID at once, so a
re-fetched corpus or a hand edit can't silently weaken the set.
"""

from __future__ import annotations

import json
import random
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Literal

import yaml

from enterprise_rag.data import DocPage, DocumentRecord
from enterprise_rag.evaluation.evidence import quote_in_text

QUOTE_MIN_WORDS = 10
QUOTE_MAX_WORDS = 60
# A stored quote must be (near-)verbatim in its document; normalization absorbs formatting.
QUOTE_EXISTS_THRESHOLD = 0.95
_WORD = re.compile(r"\w+")

# Category -> expected behavior. Indirect-injection items are answered, just safely.
CATEGORIES: dict[str, str] = {
    "single_fact": "answer",
    "general_page": "answer",
    "multi_hop": "answer",
    "sec_lookup": "answer",
    "spreadsheet_lookup": "answer",
    "cross_source_finance": "answer",
    "c_level": "answer",
    "indirect_injection": "answer",
    "cross_role": "refuse",
    "out_of_scope": "refuse",
    "direct_injection": "refuse",
}


class GoldenValidationError(ValueError):
    pass


@dataclass(frozen=True)
class Evidence:
    doc_id: str
    quote: str
    page: int | None = None


@dataclass(frozen=True)
class NumericAnswer:
    value: float
    unit: str
    scale: int  # value × scale = the amount in `unit`, e.g. thousands of USD → 1000


@dataclass(frozen=True)
class GoldenItem:
    id: str
    question: str
    asked_as: str
    category: str
    expected_behavior: Literal["answer", "refuse"]
    reference_answer: str
    numeric_answer: NumericAnswer | None
    gold_evidence: tuple[Evidence, ...]
    forbidden_doc_ids: tuple[str, ...]
    split: Literal["dev", "test"] | None
    notes: str


def word_count(text: str) -> int:
    return len(_WORD.findall(text))


def item_from_dict(d: dict) -> GoldenItem:
    num = d.get("numeric_answer")
    return GoldenItem(
        id=d["id"],
        question=d["question"],
        asked_as=d["asked_as"],
        category=d["category"],
        expected_behavior=d["expected_behavior"],
        reference_answer=d.get("reference_answer", ""),
        numeric_answer=NumericAnswer(**num) if num else None,
        gold_evidence=tuple(Evidence(**e) for e in d.get("gold_evidence", ())),
        forbidden_doc_ids=tuple(d.get("forbidden_doc_ids", ())),
        split=d.get("split"),
        notes=d.get("notes", ""),
    )


def load_golden(path: Path) -> list[GoldenItem]:
    return [item_from_dict(json.loads(line)) for line in path.read_text().splitlines()
            if line.strip()]


def load_handwritten(path: Path) -> list[GoldenItem]:
    """Hand-written items live in YAML so multi-line quotes and questions stay readable."""
    return [item_from_dict(d) for d in yaml.safe_load(path.read_text())["items"]]


def save_golden(path: Path, items: Iterable[GoldenItem]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(asdict(i), ensure_ascii=False) + "\n" for i in items))


def assign_splits(items: Sequence[GoldenItem], seed: int) -> list[GoldenItem]:
    """Half of each category (rounded down) goes to dev, the rest to test; order is kept."""
    by_cat: dict[str, list[str]] = defaultdict(list)
    for item in sorted(items, key=lambda i: i.id):
        by_cat[item.category].append(item.id)
    rng = random.Random(seed)
    split_of: dict[str, str] = {}
    for cat in sorted(by_cat):
        ids = by_cat[cat]
        rng.shuffle(ids)
        n_dev = len(ids) // 2
        split_of.update({i: ("dev" if k < n_dev else "test") for k, i in enumerate(ids)})
    return [replace(i, split=split_of[i.id]) for i in items]


def validate_golden(
    items: Sequence[GoldenItem],
    manifest: Sequence[DocumentRecord],
    doc_texts: Mapping[str, Sequence[DocPage]],
    roles: Sequence[str],
) -> None:
    """Raise one GoldenValidationError naming every item that breaks a rule."""
    allowed = {r.doc_id: set(r.allowed_roles) for r in manifest}
    errors: list[str] = []
    seen_ids: set[str] = set()
    for item in items:
        errors += [f"{item.id}: {msg}" for msg in _item_errors(item, allowed, doc_texts, roles)]
        if item.id in seen_ids:
            errors.append(f"{item.id}: duplicate id")
        seen_ids.add(item.id)
    if errors:
        raise GoldenValidationError(f"{len(errors)} golden-set problems:\n" + "\n".join(errors))


def _quote_exists(ev: Evidence, doc_texts: Mapping[str, Sequence[DocPage]]) -> bool:
    pages = [p for p in doc_texts.get(ev.doc_id, ()) if ev.page is None or p.page == ev.page]
    return any(quote_in_text(ev.quote, p.text, QUOTE_EXISTS_THRESHOLD) for p in pages)


def _item_errors(item, allowed, doc_texts, roles) -> list[str]:
    errs = []
    if item.asked_as not in roles:
        errs.append(f"unknown role {item.asked_as!r}")
    if item.category not in CATEGORIES:
        errs.append(f"unknown category {item.category!r}")
    elif CATEGORIES[item.category] != item.expected_behavior:
        errs.append(f"{item.category} items must be {CATEGORIES[item.category]!r}")
    if not item.question.strip():
        errs.append("empty question")

    if item.expected_behavior == "answer":
        if not item.gold_evidence:
            errs.append("answer item has no gold evidence")
        if not item.reference_answer.strip():
            errs.append("answer item has no reference answer")
    for ev in item.gold_evidence:
        n = word_count(ev.quote)
        if not QUOTE_MIN_WORDS <= n <= QUOTE_MAX_WORDS:
            errs.append(f"quote from {ev.doc_id} has {n} words (needs "
                        f"{QUOTE_MIN_WORDS}-{QUOTE_MAX_WORDS})")
        if ev.doc_id not in allowed and ev.doc_id not in doc_texts:
            errs.append(f"unknown doc_id {ev.doc_id!r}")
        elif ev.doc_id in allowed and item.asked_as not in allowed[ev.doc_id]:
            errs.append(f"{item.asked_as} can't see its own evidence {ev.doc_id}")
        if not _quote_exists(ev, doc_texts):
            errs.append(f"quote not found in {ev.doc_id} (page {ev.page}): {ev.quote[:60]!r}")

    if item.category == "cross_role" and not item.forbidden_doc_ids:
        errs.append("cross-role item has no forbidden_doc_ids")
    for doc_id in item.forbidden_doc_ids:
        if doc_id not in allowed:
            errs.append(f"unknown forbidden doc_id {doc_id!r}")
        elif item.asked_as in allowed[doc_id]:
            errs.append(f"{item.asked_as} can see forbidden doc {doc_id}")
    return errs
