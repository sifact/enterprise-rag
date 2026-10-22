"""Generate the fictional finance spreadsheets (budget, headcount, vendor spend).

The workbooks are generated from one seeded model so they agree with each other: budgeted
salaries come from the headcount plan. That makes cross-file golden questions possible
("cost per engineer in Q2"). Every workbook opens with an About sheet saying the numbers are fictional.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

from enterprise_rag.config import DataConfig
from enterprise_rag.data.manifest import DocumentRecord, allowed_roles_for, sha256_file

log = logging.getLogger(__name__)

SOURCE = "synthetic"
FISCAL_YEAR = "FY2027"  # GitLab's fiscal year runs Feb-Jan; FY2027 = Feb 2026 - Jan 2027
QUARTERS = ("Q1", "Q2", "Q3", "Q4")
ACTUAL_QUARTERS = ("Q1", "Q2")  # matches the latest 10-Q (period ending 2026-07-31)

# department: (starting headcount, fully loaded annual cost per head in USD)
DEPARTMENTS: dict[str, tuple[int, int]] = {
    "Engineering": (820, 210_000),
    "Product": (140, 200_000),
    "Sales": (520, 190_000),
    "Marketing": (210, 170_000),
    "Customer Success": (260, 150_000),
    "G&A": (300, 165_000),
}
REGION_SHARE = {"AMER": 0.55, "EMEA": 0.30, "APAC": 0.15}
LEVEL_SHARE = {"IC1": 0.08, "IC2": 0.22, "IC3": 0.30, "IC4": 0.17, "IC5": 0.06,
               "Manager": 0.11, "Director": 0.05, "VP": 0.01}
# Non-salary opex as a share of salaries, per line item (before noise).
OPEX_LINES = {"Contractors": 0.06, "Software & tools": 0.05, "Travel": 0.02,
              "Marketing programs": 0.0, "Facilities & other": 0.03}
MARKETING_PROGRAMS_SHARE = 0.9  # marketing spends roughly its payroll again on programs
VENDORS = [  # fictional names
    ("Northwind Cloud", "Cloud hosting", "Engineering"),
    ("Bluepeak Compute", "Cloud hosting", "Engineering"),
    ("Ledgerline", "SaaS tools", "G&A"),
    ("Pipewise CRM", "SaaS tools", "Sales"),
    ("Brightcast Media", "Marketing agencies", "Marketing"),
    ("Eventory", "Events", "Marketing"),
    ("Talentbridge", "Recruiting", "G&A"),
    ("Clearcounsel LLP", "Professional services", "G&A"),
    ("Auditwell", "Professional services", "G&A"),
    ("Supportly", "SaaS tools", "Customer Success"),
    ("Codeguard", "Security tools", "Engineering"),
    ("Travelnest", "Travel", "G&A"),
]

Workbook = dict[str, pd.DataFrame]


FICTIONAL_NOTICE = "FICTIONAL DATA generated for the enterprise-rag demo. Not GitLab Inc. data."


def _about(cfg: DataConfig, description: str) -> pd.DataFrame:
    return pd.DataFrame({"Field": ["Notice", "Contents", "Fiscal year", "Generator seed"],
                         "Value": [FICTIONAL_NOTICE, description, FISCAL_YEAR, cfg.seed]})


def headcount_model(rng: np.random.Generator) -> pd.DataFrame:
    """Quarter-end headcount per department/region/level; Q1-Q2 actual, Q3-Q4 plan."""
    rows = []
    for dept, (base, _) in DEPARTMENTS.items():
        growth = rng.uniform(0.01, 0.05, size=len(QUARTERS))
        totals = np.round(base * np.cumprod(1 + growth)).astype(int)
        for q, total in zip(QUARTERS, totals):
            split = rng.multinomial(total, list(REGION_SHARE.values()))
            for region, n_region in zip(REGION_SHARE, split):
                levels = rng.multinomial(n_region, list(LEVEL_SHARE.values()))
                for level, n in zip(LEVEL_SHARE, levels):
                    rows.append((dept, region, level, q, int(n)))
    df = pd.DataFrame(rows, columns=["Department", "Region", "Level", "Quarter", "Headcount"])
    df["Type"] = np.where(df["Quarter"].isin(ACTUAL_QUARTERS), "Actual", "Plan")
    return df


def build_headcount(cfg: DataConfig, hc: pd.DataFrame, rng: np.random.Generator) -> Workbook:
    wide = (hc.pivot_table(index=["Department", "Region", "Level"], columns="Quarter",
                           values="Headcount", aggfunc="sum")
            .reindex(columns=list(QUARTERS)).reset_index())
    wide.columns = ["Department", "Region", "Level",
                    *[f"{q} {'actual' if q in ACTUAL_QUARTERS else 'plan'}" for q in QUARTERS]]
    by_dept = hc.groupby(["Department", "Quarter"])["Headcount"].sum().unstack()[list(QUARTERS)]
    net_adds = by_dept.diff(axis=1).fillna(0).astype(int)
    attrition = (by_dept * rng.uniform(0.02, 0.04, size=by_dept.shape)).round().astype(int)
    hiring = pd.DataFrame({
        "Department": np.repeat(by_dept.index, len(QUARTERS)),
        "Quarter": list(QUARTERS) * len(by_dept),
        "Planned hires": (net_adds + attrition).to_numpy().ravel(),
        "Expected attrition": attrition.to_numpy().ravel(),
    })
    hiring["Open reqs at quarter start"] = (hiring["Planned hires"] * 0.6).round().astype(int)
    return {"About": _about(cfg, "Headcount by department, region and level; hiring plan"),
            "Headcount": wide, "Hiring plan": hiring}


def build_budget(cfg: DataConfig, hc: pd.DataFrame, rng: np.random.Generator) -> Workbook:
    """Plan for all quarters, actuals for Q1-Q2. Salaries = headcount x loaded cost / 4."""
    dept_hc = hc.groupby(["Department", "Quarter"])["Headcount"].sum()
    rows = []
    for dept, (_, cost) in DEPARTMENTS.items():
        for q in QUARTERS:
            salaries = dept_hc[(dept, q)] * cost / 4
            lines = {"Salaries & benefits": salaries}
            for line, share in OPEX_LINES.items():
                if line == "Marketing programs":
                    share = MARKETING_PROGRAMS_SHARE if dept == "Marketing" else 0.0
                lines[line] = salaries * share * rng.uniform(0.85, 1.15)
            for line, plan in lines.items():
                actual = plan * rng.normal(1.0, 0.06) if q in ACTUAL_QUARTERS else np.nan
                rows.append((dept, line, q, round(plan, -3), round(actual, -3)))
    long = pd.DataFrame(rows, columns=["Department", "Line item", "Quarter", "Plan", "Actual"])
    long = long[long["Plan"] > 0]
    wide = long.pivot_table(index=["Department", "Line item"], columns="Quarter",
                            values=["Plan", "Actual"], aggfunc="sum", dropna=False)
    cols = [("Plan", q) for q in QUARTERS] + [("Actual", q) for q in ACTUAL_QUARTERS]
    wide = wide[cols]
    wide.columns = [f"{q} {kind.lower()} (USD)" for kind, q in cols]
    wide = wide.reset_index()
    for q in ACTUAL_QUARTERS:
        wide[f"{q} variance (USD)"] = wide[f"{q} actual (USD)"] - wide[f"{q} plan (USD)"]
    summary = (long.groupby("Department")[["Plan", "Actual"]].sum(min_count=1)
               .rename(columns={"Plan": "FY plan (USD)", "Actual": "H1 actual (USD)"}).reset_index())
    return {"About": _about(cfg, "Opex budget by department, line item and quarter"),
            "Budget": wide, "Summary": summary}


def build_vendor_spend(cfg: DataConfig, rng: np.random.Generator) -> Workbook:
    rows = []
    for name, category, dept in VENDORS:
        annual = float(rng.lognormal(mean=13.0, sigma=0.8))  # ~$450k median
        q_plan = annual / 4
        actuals = [round(q_plan * rng.normal(1.0, 0.1), -2) for _ in ACTUAL_QUARTERS]
        rows.append((name, category, dept, round(annual, -3), *actuals))
    df = pd.DataFrame(rows, columns=["Vendor", "Category", "Owning department", "FY plan (USD)",
                                     *[f"{q} actual (USD)" for q in ACTUAL_QUARTERS]])
    return {"About": _about(cfg, "Top vendors by category and quarter"),
            "Vendor spend": df.sort_values("FY plan (USD)", ascending=False, ignore_index=True)}


def build_workbooks(cfg: DataConfig) -> dict[str, Workbook]:
    """All workbooks from one RNG stream, in a fixed order, so output depends only on the seed."""
    rng = np.random.default_rng(cfg.seed)
    hc = headcount_model(rng)
    builders: dict[str, Callable[[], Workbook]] = {
        "headcount_fy2027.xlsx": lambda: build_headcount(cfg, hc, rng),
        "budget_fy2027.xlsx": lambda: build_budget(cfg, hc, rng),
        "vendor_spend_fy2027.xlsx": lambda: build_vendor_spend(cfg, rng),
    }
    unknown = {f.name for f in cfg.synthetic.files} - builders.keys()
    if unknown:
        raise ValueError(f"No generator for synthetic files: {sorted(unknown)}")
    return {name: build() for name, build in builders.items()
            if name in {f.name for f in cfg.synthetic.files}}


def _write_xlsx(path: Path, workbook: Workbook) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet, df in workbook.items():
            df.to_excel(writer, sheet_name=sheet, index=False)


def fetch_synthetic(cfg: DataConfig) -> list[DocumentRecord]:
    out_dir = cfg.raw_dir / SOURCE
    out_dir.mkdir(parents=True, exist_ok=True)
    descriptions = {f.name: f.contents for f in cfg.synthetic.files}
    records = []
    for name, workbook in build_workbooks(cfg).items():
        path = out_dir / name
        _write_xlsx(path, workbook)
        log.info("Wrote %s (%s)", path.name, ", ".join(workbook))
        records.append(
            DocumentRecord(
                doc_id=f"{SOURCE}:{name.removesuffix('.xlsx')}",
                source=SOURCE,
                path=path.relative_to(cfg.raw_dir).as_posix(),
                title=f"{descriptions[name].capitalize()} ({FISCAL_YEAR}, fictional)",
                source_url=None,
                department=cfg.synthetic.role,
                allowed_roles=allowed_roles_for(cfg.synthetic.role, cfg),
                license="project-generated (fictional)",
                content_hash=sha256_file(path),
            )
        )
    return records
