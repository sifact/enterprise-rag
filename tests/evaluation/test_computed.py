import pytest

from enterprise_rag.data import build_workbooks, fetch_synthetic, load_doc_pages
from enterprise_rag.evaluation import computed_items, validate_golden


def by_id(cfg):
    return {i.id: i for i in computed_items(cfg)}


def test_counts_ids_and_role(cfg):
    items = computed_items(cfg)
    assert [i.id for i in items] == [f"fin-xlsx-00{n}" for n in range(1, 7)] + [
        "fin-cross-001", "fin-cross-002"]
    assert {i.asked_as for i in items} == {"finance"}
    assert sum(i.category == "spreadsheet_lookup" for i in items) == 6
    assert sum(i.category == "cross_source_finance" for i in items) == 2
    assert all(i.numeric_answer is not None for i in items)


def test_computed_items_match_workbook_values(cfg):
    budget = build_workbooks(cfg)["budget_fy2027.xlsx"]["Budget"]
    row = budget[(budget["Department"] == "Engineering")
                 & (budget["Line item"] == "Salaries & benefits")].iloc[0]
    expected = abs(row["Q2 actual (USD)"] - row["Q2 plan (USD)"])
    assert by_id(cfg)["fin-xlsx-001"].numeric_answer.value == pytest.approx(expected)

    books = build_workbooks(cfg)
    vendors = books["vendor_spend_fy2027.xlsx"]["Vendor spend"].set_index("Vendor")
    summary = books["budget_fy2027.xlsx"]["Summary"].set_index("Department")
    share = 100 * vendors.loc["Supportly", "FY plan (USD)"] / summary.loc[
        "Customer Success", "FY plan (USD)"]
    assert by_id(cfg)["fin-cross-001"].numeric_answer.value == pytest.approx(share, abs=0.01)


def test_computed_items_validate(cfg):
    records = fetch_synthetic(cfg)
    doc_texts = {r.doc_id: load_doc_pages(r, cfg.raw_dir) for r in records}
    validate_golden(computed_items(cfg), records, doc_texts, cfg.roles)


def test_computed_items_are_deterministic(cfg):
    assert computed_items(cfg) == computed_items(cfg)
