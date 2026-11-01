"""Merge reviewed drafts, computed and hand-written items, derive role twins, freeze the set.

Cross-role and c_level items are derived from answerable items rather than written, so each
"refuse" item has a twin whose gold answer is exactly what must not leak.
"""

from __future__ import annotations

import random
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import replace
from itertools import cycle, islice
from pathlib import Path

from enterprise_rag.data import DocPage, DocumentRecord
from enterprise_rag.evaluation.golden import GoldenItem, assign_splits, validate_golden

CROSS_ROLE_COUNT = 12
C_LEVEL_COUNT = 4
SPOT_CHECK_SHARE = 0.2
DECISIONS = ("accept", "edit", "drop")
_CHECKED = re.compile(r"^- \[[xX]\] (accept|edit|drop)\s*$", re.MULTILINE)
_NOTE = re.compile(r"^Review note:[ \t]*(.*)$", re.MULTILINE)


class UnreviewedDraftError(ValueError):
    pass


# --- Review decisions ---------------------------------------------------------------------


def parse_review_decisions(path: Path) -> dict[str, tuple[str, str]]:
    """Item ID -> (decision, review note) for every section with exactly one ticked box."""
    decisions = {}
    for section in path.read_text().split("\n## ")[1:]:
        item_id = section.splitlines()[0].strip()
        ticked = _CHECKED.findall(section)
        if len(ticked) > 1:
            raise ValueError(f"{item_id}: more than one box ticked: {ticked}")
        if ticked:
            note = _NOTE.search(section)
            decisions[item_id] = (ticked[0], note.group(1).strip() if note else "")
    return decisions


def reviewed_drafts(drafts: Sequence[GoldenItem],
                    decisions: Mapping[str, tuple[str, str]]) -> list[GoldenItem]:
    """Accepted and edited drafts; refuses to proceed while any draft is undecided."""
    missing = [d.id for d in drafts if d.id not in decisions]
    if missing:
        raise UnreviewedDraftError(f"{len(missing)} drafts not reviewed: {', '.join(missing)}")
    kept = []
    for draft in drafts:
        decision, note = decisions[draft.id]
        if decision == "accept":
            kept.append(draft)
        elif decision == "edit":
            kept.append(replace(draft, notes=f"{draft.notes}; edited in review: {note}"))
    return kept


def spot_check_ids(items: Sequence[GoldenItem], seed: int,
                   share: float = SPOT_CHECK_SHARE) -> list[str]:
    """The random sample the user reviews before the set is frozen."""
    ids = sorted(i.id for i in items)
    return sorted(random.Random(seed).sample(ids, round(len(ids) * share)))


# --- Deriving role twins ------------------------------------------------------------------


def _visibility(manifest: Sequence[DocumentRecord]) -> dict[str, set[str]]:
    return {r.doc_id: set(r.allowed_roles) for r in manifest}


def _owned_candidates(answerable, allowed, roles) -> list[GoldenItem]:
    """Items whose evidence is all in department-owned manifest docs (not company-wide)."""
    everyone = set(roles)
    return [
        i for i in sorted(answerable, key=lambda i: i.id)
        if i.gold_evidence
        and all(ev.doc_id in allowed and allowed[ev.doc_id] != everyone for ev in i.gold_evidence)
    ]


def derive_cross_role(answerable: Sequence[GoldenItem], manifest: Sequence[DocumentRecord],
                      roles: Sequence[str], superuser: str, seed: int) -> list[GoldenItem]:
    """Re-ask answerable questions as roles that can see none of the gold documents."""
    allowed = _visibility(manifest)
    candidates = _owned_candidates(answerable, allowed, roles)
    random.Random(seed).shuffle(candidates)
    askers = sorted(r for r in roles if r != superuser)
    used: set[str] = set()
    out = []
    for n, role in enumerate(islice(cycle(askers), CROSS_ROLE_COUNT), start=1):
        twin = next((c for c in candidates if c.id not in used and
                     all(role not in allowed[ev.doc_id] for ev in c.gold_evidence)), None)
        if twin is None:
            raise ValueError(f"No answerable item left that {role} cannot see")
        used.add(twin.id)
        out.append(replace(
            twin, id=f"xrole-{n:03d}", asked_as=role, category="cross_role",
            expected_behavior="refuse", reference_answer="", numeric_answer=None,
            gold_evidence=(),
            forbidden_doc_ids=tuple(sorted({e.doc_id for e in twin.gold_evidence})),
            split=None, notes=f"twin: {twin.id}; derived cross-role item",
        ))
    return out


def derive_c_level(answerable: Sequence[GoldenItem], manifest: Sequence[DocumentRecord],
                   superuser: str, seed: int) -> list[GoldenItem]:
    """Department questions re-asked by the superuser, one per department, still answered."""
    allowed = _visibility(manifest)
    all_roles = set().union(*allowed.values())
    by_owner: dict[str, list[GoldenItem]] = defaultdict(list)
    for item in _owned_candidates(answerable, allowed, all_roles):
        owners = allowed[item.gold_evidence[0].doc_id] - {superuser}
        by_owner[min(owners)].append(item)
    rng = random.Random(seed)
    out = []
    for n, owner in enumerate(rng.sample(sorted(by_owner), C_LEVEL_COUNT), start=1):
        twin = rng.choice(by_owner[owner])
        out.append(replace(twin, id=f"clevel-{n:03d}", asked_as=superuser, category="c_level",
                           split=None, notes=f"twin: {twin.id}; derived c_level item"))
    return out


# --- Assembly -----------------------------------------------------------------------------


def assemble(
    drafts: Sequence[GoldenItem],
    computed: Sequence[GoldenItem],
    handwritten: Sequence[GoldenItem],
    manifest: Sequence[DocumentRecord],
    doc_texts: Mapping[str, Sequence[DocPage]],
    roles: Sequence[str],
    superuser: str,
    seed: int,
) -> list[GoldenItem]:
    """Merge every source, derive twins, split, and validate the whole set."""
    base = [*drafts, *computed, *handwritten]
    answerable = [i for i in base
                  if i.expected_behavior == "answer" and i.category != "indirect_injection"]
    items = [*base,
             *derive_c_level(answerable, manifest, superuser, seed),
             *derive_cross_role(answerable, manifest, roles, superuser, seed)]
    items = assign_splits(items, seed)
    validate_golden(items, manifest, doc_texts, roles)
    return items
