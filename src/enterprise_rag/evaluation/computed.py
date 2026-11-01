"""Spreadsheet and cross-file finance items whose gold answers are computed, not drafted.

An LLM would happily invent a plausible budget figure, so every number here comes from the
same DataFrames the workbooks are written from. Evidence quotes are cut from each sheet as
`sheet_to_text` renders it after an Excel round trip, so validation finds them verbatim.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import pandas as pd

from enterprise_rag.config import DataConfig
from enterprise_rag.data import build_workbooks, sheet_to_text
from enterprise_rag.evaluation.golden import (
    QUOTE_MAX_WORDS,
    QUOTE_MIN_WORDS,
    Evidence,
    GoldenItem,
    NumericAnswer,
    word_count,
)

ROLE = "finance"
NOTE = "computed from the synthetic workbooks with pandas (computed.py)"


@dataclass(frozen=True)
class _Sheet:
    doc_id: str
    page: int  # 1-based sheet position, as load_doc_pages numbers it
    df: pd.DataFrame
    text: str

    def row(self, **match) -> int:
        mask = pd.Series(True, index=self.df.index)
        for col, value in match.items():
            mask &= self.df[col] == value
        hits = self.df.index[mask]
        if len(hits) != 1:
            raise ValueError(f"{self.doc_id} p{self.page}: {match} matched {len(hits)} rows")
        return int(hits[0])

    def value(self, column: str, **match) -> float:
        return float(self.df.loc[self.row(**match), column])

    def evidence(self, **match) -> Evidence:
        return Evidence(self.doc_id, _row_quote(self.text, self.row(**match)), self.page)


def _round_trip(workbook: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Write and re-read the workbook so dtypes (e.g. floats beside NaN) match the files."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, df in workbook.items():
            df.to_excel(writer, sheet_name=name, index=False)
    buf.seek(0)
    return pd.read_excel(buf, sheet_name=None)


def _load_sheets(cfg: DataConfig) -> dict[tuple[str, str], _Sheet]:
    sheets = {}
    for filename, workbook in build_workbooks(cfg).items():
        doc_id = f"synthetic:{filename.removesuffix('.xlsx')}"
        for page, (name, df) in enumerate(_round_trip(workbook).items(), start=1):
            sheets[(doc_id, name)] = _Sheet(doc_id, page, df, sheet_to_text(name, df))
    return sheets


def _row_quote(sheet_text: str, row_pos: int) -> str:
    """The data row's CSV line, widened with neighbouring lines until it is 10+ words."""
    lines = sheet_text.splitlines()
    lo = hi = row_pos + 2  # line 0 is "Sheet: <name>", line 1 the header
    while word_count("\n".join(lines[lo : hi + 1])) < QUOTE_MIN_WORDS:
        if hi + 1 < len(lines):
            hi += 1
        elif lo > 1:
            lo -= 1
        else:
            break
    quote = "\n".join(lines[lo : hi + 1])
    if word_count(quote) > QUOTE_MAX_WORDS:
        raise ValueError(f"Row quote too long: {quote[:80]!r}")
    return quote


def _usd(x: float) -> str:
    return f"${x:,.0f}"


def _item(id_: str, category: str, question: str, answer: str, value: float, unit: str,
          evidence: list[Evidence]) -> GoldenItem:
    return GoldenItem(
        id=id_, question=question, asked_as=ROLE, category=category, expected_behavior="answer",
        reference_answer=answer, numeric_answer=NumericAnswer(round(value, 2), unit, 1),
        gold_evidence=tuple(evidence), forbidden_doc_ids=(), split=None, notes=NOTE,
    )


def computed_items(cfg: DataConfig) -> list[GoldenItem]:
    s = _load_sheets(cfg)
    budget = s[("synthetic:budget_fy2027", "Budget")]
    summary = s[("synthetic:budget_fy2027", "Summary")]
    hiring = s[("synthetic:headcount_fy2027", "Hiring plan")]
    vendors = s[("synthetic:vendor_spend_fy2027", "Vendor spend")]
    items = []

    eng_sal = {"Department": "Engineering", "Line item": "Salaries & benefits"}
    plan, actual = budget.value("Q2 plan (USD)", **eng_sal), budget.value("Q2 actual (USD)",
                                                                           **eng_sal)
    diff = actual - plan
    items.append(_item(
        "fin-xlsx-001", "spreadsheet_lookup",
        "By how much did Engineering's salaries and benefits in Q2 come in over or under plan?",
        f"Engineering's Q2 salaries and benefits were {_usd(actual)} against a plan of "
        f"{_usd(plan)}, {_usd(abs(diff))} {'over' if diff > 0 else 'under'} plan.",
        abs(diff), "USD", [budget.evidence(**eng_sal)]))

    mkt = {"Department": "Marketing", "Line item": "Marketing programs"}
    value = budget.value("Q3 plan (USD)", **mkt)
    items.append(_item(
        "fin-xlsx-002", "spreadsheet_lookup",
        "What is Marketing's planned spend on marketing programs for the third quarter?",
        f"Marketing plans {_usd(value)} for marketing programs in Q3.",
        value, "USD", [budget.evidence(**mkt)]))

    value = summary.value("FY plan (USD)", Department="G&A")
    items.append(_item(
        "fin-xlsx-003", "spreadsheet_lookup",
        "What's the total operating budget planned for G&A this fiscal year?",
        f"G&A's full-year FY2027 opex plan is {_usd(value)}.",
        value, "USD", [summary.evidence(Department="G&A")]))

    sales_q3 = {"Department": "Sales", "Quarter": "Q3"}
    value = hiring.value("Planned hires", **sales_q3)
    attrition = hiring.value("Expected attrition", **sales_q3)
    items.append(_item(
        "fin-xlsx-004", "spreadsheet_lookup",
        "How many people is Sales planning to hire in Q3?",
        f"Sales plans {value:.0f} hires in Q3, against {attrition:.0f} expected departures.",
        value, "people", [hiring.evidence(**sales_q3)]))

    cloud = vendors.df[vendors.df["Category"] == "Cloud hosting"]
    top = cloud.sort_values("FY plan (USD)", ascending=False).iloc[0]["Vendor"]
    value = vendors.value("FY plan (USD)", Vendor=top)
    items.append(_item(
        "fin-xlsx-005", "spreadsheet_lookup",
        "Which cloud hosting provider has the largest annual plan, and how much is it?",
        f"{top} is the largest cloud hosting vendor, with an FY2027 plan of {_usd(value)}.",
        value, "USD", [vendors.evidence(Vendor=top)]))

    value = vendors.value("Q1 actual (USD)", Vendor="Supportly")
    items.append(_item(
        "fin-xlsx-006", "spreadsheet_lookup",
        "How much did we actually pay Supportly in the first quarter?",
        f"Actual Q1 spend with Supportly was {_usd(value)}.",
        value, "USD", [vendors.evidence(Vendor="Supportly")]))

    vendor_plan = vendors.value("FY plan (USD)", Vendor="Supportly")
    dept_plan = summary.value("FY plan (USD)", Department="Customer Success")
    share = 100 * vendor_plan / dept_plan
    items.append(_item(
        "fin-cross-001", "cross_source_finance",
        "What percentage of Customer Success's annual budget is planned for Supportly?",
        f"Supportly's FY plan of {_usd(vendor_plan)} is {share:.2f}% of Customer Success's "
        f"{_usd(dept_plan)} full-year plan.",
        share, "%", [vendors.evidence(Vendor="Supportly"),
                     summary.evidence(Department="Customer Success")]))

    nw = vendors.value("Q1 actual (USD)", Vendor="Northwind Cloud") + vendors.value(
        "Q2 actual (USD)", Vendor="Northwind Cloud")
    eng_h1 = summary.value("H1 actual (USD)", Department="Engineering")
    share = 100 * nw / eng_h1
    items.append(_item(
        "fin-cross-002", "cross_source_finance",
        "What share of Engineering's first-half actual spending went to Northwind Cloud?",
        f"Northwind Cloud's Q1 and Q2 actuals total {_usd(nw)}, which is {share:.2f}% of "
        f"Engineering's H1 actual spend of {_usd(eng_h1)}.",
        share, "%", [vendors.evidence(Vendor="Northwind Cloud"),
                     summary.evidence(Department="Engineering")]))
    return items
