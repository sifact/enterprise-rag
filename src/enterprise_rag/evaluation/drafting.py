"""Draft answerable golden items from sampled corpus passages with an LLM.

Drafts are cheap and often flawed, so every one passes automatic checks here (the quote is
really in the passage, the question doesn't copy it, no duplicates) and is then reviewed by
hand in the review file before anything reaches the frozen set.
"""

from __future__ import annotations

import json
import logging
import math
import random
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from itertools import pairwise
from pathlib import Path

from enterprise_rag.data import DocumentRecord, load_doc_pages
from enterprise_rag.data.handbook_pages import prose_word_count
from enterprise_rag.evaluation.answer_metrics import numeric_match
from enterprise_rag.evaluation.evidence import quote_in_text
from enterprise_rag.evaluation.golden import (
    QUOTE_MAX_WORDS,
    QUOTE_MIN_WORDS,
    Evidence,
    GoldenItem,
    NumericAnswer,
    word_count,
)
from enterprise_rag.llm import LLMError

log = logging.getLogger(__name__)

PROMPT_VERSION = "draft-v2"
QUOTE_FOUND_THRESHOLD = 0.95
MAX_QUESTION_QUOTE_OVERLAP = 0.5  # share of the question's word 4-grams found in a quote
MIN_SECTION_WORDS = 80
MAX_PASSAGE_WORDS = 450
SEC_FIRST_PAGE = 5  # skip the cover and table of contents
SEC_MIN_PAGE_WORDS = 150
_TOTAL_ROW = re.compile(r"^\s*Total\b.*\d", re.MULTILINE)
_HEADING = re.compile(r"^#{1,4} ", re.MULTILINE)
_TOKEN = re.compile(r"\w+")
ID_PREFIX = {"engineering": "eng", "hr": "hr", "marketing": "mkt", "legal": "legal",
             "sales": "sales", "finance": "fin"}

SYSTEM_PROMPT = f"""You write test questions for an internal company assistant. Prompt version: {PROMPT_VERSION}.
You get one or more PASSAGES from company documents and the ROLE of the employee asking.
Write ONE question that this employee might realistically ask, which the passages answer.
Rules:
- The question must be answerable only from the passages, with one clear correct answer.
- Paraphrase. Do not reuse the passage's wording or copy phrases from it.
- Do not mention "the passage", "the document" or "the text" in the question.
- "quotes" must be copied EXACTLY, character for character, from the passages: one quote per
  passage, each ONE continuous span of 15-50 words that contains the answer. Never skip text
  inside a quote and never use "..." in a quote. For a table, quote the consecutive lines that
  hold the answer row, starting a few lines above it if needed to reach 15 words.
- If several passages are given, write ONE question whose answer combines facts from every
  passage (e.g. compares them, or uses one to apply the other). Never join two unrelated
  questions with "and". If the passages share no natural connection, reply with
  {{"question": null, "answer": null, "quotes": [], "number": null}}.
- "answer" is one or two full sentences with units, e.g. "$9.8 million (9,774 in thousands)".
- For numbers from financial statements, also return "number" with "value" as written in the
  quote (no commas), "unit" (e.g. "USD", "%", "customers") and "scale" (1, 1000 for
  "in thousands", 1000000 for "in millions"). Otherwise set "number" to null.
Reply with JSON only: {{"question": str, "answer": str, "quotes": [str, ...], "number": object|null}}"""


@dataclass(frozen=True)
class Passage:
    id: str
    category: str
    bucket: str  # quota key, e.g. "single_fact:legal"
    asked_as: str
    doc_ids: tuple[str, ...]
    pages: tuple[int | None, ...]
    texts: tuple[str, ...]


@dataclass(frozen=True)
class DraftPlan:
    """How many accepted drafts each bucket needs; sampling over-draws by `oversample`."""

    single_fact_per_department: int = 4
    departments: tuple[str, ...] = ("engineering", "hr", "marketing", "legal", "sales", "finance")
    general_page: int = 6
    multi_hop: int = 6
    sec_lookup_10k: int = 4
    sec_lookup_10q: int = 4
    oversample: float = 1.5
    sec_role: str = "finance"

    def quotas(self) -> dict[str, int]:
        q = {f"single_fact:{d}": self.single_fact_per_department for d in self.departments}
        q |= {"general_page": self.general_page, "multi_hop": self.multi_hop,
              "sec_lookup:10-K": self.sec_lookup_10k, "sec_lookup:10-Q": self.sec_lookup_10q}
        return {k: v for k, v in q.items() if v > 0}

    def draws(self, n: int) -> int:
        return math.ceil(n * self.oversample)


# --- Sampling -----------------------------------------------------------------------------


def _sections(text: str) -> list[str]:
    """Heading-delimited sections with enough prose, each trimmed to whole paragraphs."""
    starts = [0, *(m.start() for m in _HEADING.finditer(text)), len(text)]
    out = []
    for a, b in pairwise(starts):
        section = text[a:b].strip()
        if prose_word_count(section) >= MIN_SECTION_WORDS:
            out.append(_trim(section))
    return out


def _trim(section: str) -> str:
    """Keep whole paragraphs up to MAX_PASSAGE_WORDS; the result stays a substring."""
    end = 0
    for m in re.finditer(r"\n\s*\n|\Z", section):
        if word_count(section[: m.start()]) > MAX_PASSAGE_WORDS and end:
            break
        end = m.start()
    return section[:end].strip()


def _page_sections(rec: DocumentRecord, raw_dir: Path) -> list[str]:
    return _sections(load_doc_pages(rec, raw_dir)[0].text)


def _pick_sections(records, raw_dir, rng: random.Random, n: int):
    """Up to n (record, section) pairs from distinct pages, in a seeded order."""
    shuffled = sorted(records, key=lambda r: r.doc_id)
    rng.shuffle(shuffled)
    picks = []
    for rec in shuffled:
        sections = _page_sections(rec, raw_dir)
        if sections:
            picks.append((rec, rng.choice(sections)))
        if len(picks) == n:
            break
    return picks


def _sibling_pages(records: Sequence[DocumentRecord], rng: random.Random) -> list[DocumentRecord]:
    """Pages of one randomly chosen folder with 2+ pages, so the pair is likely related."""
    folders = defaultdict(list)
    for rec in records:
        folders[rec.doc_id.rsplit("/", 1)[0]].append(rec)
    groups = [g for _, g in sorted(folders.items()) if len(g) >= 2]
    return rng.choice(groups) if groups else list(records)


def sample_passages(plan: DraftPlan, manifest: Sequence[DocumentRecord], raw_dir: Path,
                    seed: int) -> list[Passage]:
    rng = random.Random(seed)
    handbook = defaultdict(list)
    for rec in manifest:
        if rec.source == "handbook":
            handbook[rec.department].append(rec)
    passages: list[Passage] = []

    for dept in plan.departments:
        for k, (rec, text) in enumerate(_pick_sections(
                handbook[dept], raw_dir, rng, plan.draws(plan.single_fact_per_department)), 1):
            passages.append(Passage(f"{ID_PREFIX.get(dept, dept)}-fact-{k:03d}", "single_fact",
                                    f"single_fact:{dept}", dept, (rec.doc_id,), (None,), (text,)))

    for k, (rec, text) in enumerate(_pick_sections(
            handbook["general"], raw_dir, rng, plan.draws(plan.general_page)), 1):
        passages.append(Passage(f"gen-{k:03d}", "general_page", "general_page",
                                rng.choice(plan.departments), (rec.doc_id,), (None,), (text,)))

    for k in range(1, plan.draws(plan.multi_hop) + 1):
        dept = plan.departments[(k - 1) % len(plan.departments)]
        pair = _pick_sections(_sibling_pages(handbook[dept], rng), raw_dir, rng, 2)
        if len(pair) == 2:
            passages.append(Passage(f"mh-{k:03d}", "multi_hop", "multi_hop", dept,
                                    tuple(r.doc_id for r, _ in pair), (None, None),
                                    tuple(t for _, t in pair)))

    sec_n = 0
    for form, n in (("10-K", plan.sec_lookup_10k), ("10-Q", plan.sec_lookup_10q)):
        if n == 0:
            continue
        for rec in sorted((r for r in manifest if r.source == "sec" and f":{form}:" in r.doc_id),
                          key=lambda r: r.doc_id):
            pages = [p for p in load_doc_pages(rec, raw_dir)
                     if p.page and p.page >= SEC_FIRST_PAGE and _TOTAL_ROW.search(p.text)
                     and word_count(p.text) >= SEC_MIN_PAGE_WORDS]
            for page in rng.sample(pages, min(len(pages), plan.draws(n))):
                sec_n += 1
                passages.append(Passage(f"fin-sec-{sec_n:03d}", "sec_lookup",
                                        f"sec_lookup:{form}", plan.sec_role, (rec.doc_id,),
                                        (page.page,), (page.text,)))
    return passages


# --- Drafting -----------------------------------------------------------------------------


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _norm_question(q: str) -> str:
    return " ".join(_tokens(q))


def _overlap(question: str, quote: str, n: int = 4) -> float:
    q, t = _tokens(question), _tokens(quote)
    q_grams = [tuple(q[i : i + n]) for i in range(len(q) - n + 1)]
    if not q_grams:
        return 0.0
    t_grams = {tuple(t[i : i + n]) for i in range(len(t) - n + 1)}
    return sum(g in t_grams for g in q_grams) / len(q_grams)


def _user_prompt(p: Passage) -> str:
    blocks = [f"PASSAGE {i} (from {doc}{f', page {page}' if page else ''}):\n{text}"
              for i, (doc, page, text) in enumerate(zip(p.doc_ids, p.pages, p.texts,
                                                        strict=True), 1)]
    return f"ROLE: {p.asked_as}\n\n" + "\n\n".join(blocks)


def _reject(p: Passage, reason: str) -> None:
    log.info("drop %s: %s", p.id, reason)


def draft_item(passage: Passage, client, seen_questions: set[str] | frozenset = frozenset()
               ) -> GoldenItem | None:
    """One LLM draft for a passage, or None (with the reason logged) if any check fails."""
    try:
        data, _ = client.complete_json(SYSTEM_PROMPT, _user_prompt(passage), temperature=0.3)
    except LLMError as exc:
        _reject(passage, f"LLM error: {exc}")
        return None

    question = str(data.get("question") or "").strip()
    answer = str(data.get("answer") or "").strip()
    quotes = [str(q).strip() for q in data.get("quotes") or []]
    if not question or not answer or len(quotes) != len(passage.texts):
        _reject(passage, f"incomplete draft: {json.dumps(data)[:200]}")
        return None
    for quote, text in zip(quotes, passage.texts, strict=True):
        if not quote_in_text(quote, text, QUOTE_FOUND_THRESHOLD):
            _reject(passage, f"quote not in passage: {quote[:80]!r}")
            return None
        n = word_count(quote)
        if not QUOTE_MIN_WORDS <= n <= QUOTE_MAX_WORDS:
            _reject(passage, f"quote has {n} words")
            return None
        if _overlap(question, quote) > MAX_QUESTION_QUOTE_OVERLAP:
            _reject(passage, f"question copies the quote: {question!r}")
            return None
    if _norm_question(question) in {_norm_question(s) for s in seen_questions}:
        _reject(passage, f"duplicate question: {question!r}")
        return None

    item = GoldenItem(
        id=passage.id, question=question, asked_as=passage.asked_as, category=passage.category,
        expected_behavior="answer", reference_answer=answer, numeric_answer=None,
        gold_evidence=tuple(Evidence(d, q, p) for d, q, p in
                            zip(passage.doc_ids, quotes, passage.pages, strict=True)),
        forbidden_doc_ids=(), split=None,
        notes=f"drafted by {client.model} ({PROMPT_VERSION})",
    )
    number = data.get("number")
    if isinstance(number, dict) and number.get("value") is not None:
        try:
            value = float(str(number["value"]).replace(",", "").replace("$", ""))
            numeric = NumericAnswer(value, str(number.get("unit") or ""),
                                    int(number.get("scale") or 1))
        except (TypeError, ValueError):
            _reject(passage, f"unreadable number: {number}")
            return None
        item = replace(item, numeric_answer=numeric)
        if not any(numeric_match(item, q, 0.005) for q in quotes):
            _reject(passage, f"number {number} not found in its quote")
            return None
    return item


def draft_all(passages: Sequence[Passage], client, quotas: Mapping[str, int],
              seen_questions: set[str] | frozenset = frozenset()) -> list[GoldenItem]:
    """Draft passages in order until each bucket's quota is met; failures only skip a passage.

    `seen_questions` carries questions from an earlier run, so a top-up run can't repeat them.
    """
    accepted: list[GoldenItem] = []
    filled: dict[str, int] = defaultdict(int)
    seen: set[str] = set(seen_questions)
    for p in passages:
        if filled[p.bucket] >= quotas.get(p.bucket, 0):
            continue
        item = draft_item(p, client, seen)
        if item is None:
            continue
        accepted.append(item)
        filled[p.bucket] += 1
        seen.add(item.question)
        log.info("kept %s (%s %d/%d)", p.id, p.bucket, filled[p.bucket], quotas[p.bucket])
    for bucket, need in quotas.items():
        if filled[bucket] < need:
            log.warning("bucket %s short: %d of %d", bucket, filled[bucket], need)
    return accepted


# --- Review file --------------------------------------------------------------------------


def write_review_file(items: Sequence[GoldenItem], path: Path, append: bool = False) -> None:
    """One section per draft with accept / edit / drop boxes for the reviewer to tick.

    `append` adds sections for top-up drafts below the existing, already-ticked ones.
    """
    header = ["# Golden set v1: draft review", "",
             ("Tick exactly one box per item. For `edit`, change the item in `v1_drafts.jsonl` "
              "and say what changed on the `Review note:` line."), ""]
    lines: list[str] = []
    for item in items:
        lines += [f"## {item.id}", "",
                  f"- Category: {item.category} · asked as `{item.asked_as}`",
                  f"- Question: {item.question}",
                  f"- Answer: {item.reference_answer}"]
        if item.numeric_answer:
            n = item.numeric_answer
            lines.append(f"- Number: {n.value:g} {n.unit} (scale {n.scale})")
        for ev in item.gold_evidence:
            page = f" p{ev.page}" if ev.page else ""
            lines.append(f"- Evidence `{ev.doc_id}`{page}: \"{' '.join(ev.quote.split())}\"")
        lines += ["", "- [ ] accept", "- [ ] edit", "- [ ] drop", "", "Review note:", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    if append and path.exists():
        path.write_text(path.read_text().rstrip() + "\n\n" + "\n".join(lines))
    else:
        path.write_text("\n".join(header + lines))
