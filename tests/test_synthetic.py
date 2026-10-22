import pandas as pd

from enterprise_rag.data import build_workbooks
from enterprise_rag.data.synthetic import ACTUAL_QUARTERS, DEPARTMENTS


def test_same_seed_gives_identical_workbooks(cfg):
    a, b = build_workbooks(cfg), build_workbooks(cfg)
    for name in a:
        for sheet in a[name]:
            pd.testing.assert_frame_equal(a[name][sheet], b[name][sheet])


def test_every_workbook_is_labelled_fictional(cfg):
    for wb in build_workbooks(cfg).values():
        assert "FICTIONAL" in wb["About"].iloc[0]["Value"]


def test_budget_salaries_follow_headcount(cfg):
    wbs = build_workbooks(cfg)
    hc = wbs["headcount_fy2027.xlsx"]["Headcount"]
    budget = wbs["budget_fy2027.xlsx"]["Budget"]
    for dept, (_, cost) in DEPARTMENTS.items():
        heads = hc.loc[hc["Department"] == dept, "Q1 actual"].sum()
        row = budget[(budget["Department"] == dept) & (budget["Line item"] == "Salaries & benefits")]
        assert abs(row["Q1 plan (USD)"].item() - heads * cost / 4) <= 500  # rounded to $1k


def test_only_actual_quarters_have_actuals(cfg):
    cols = build_workbooks(cfg)["budget_fy2027.xlsx"]["Budget"].columns
    assert [c for c in cols if "actual" in c] == [f"{q} actual (USD)" for q in ACTUAL_QUARTERS]
