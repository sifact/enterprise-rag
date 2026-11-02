from enterprise_rag.config import load_config, load_eval_config
from enterprise_rag.data import read_manifest
from enterprise_rag.evaluation import load_golden
from enterprise_rag.serving import build_meta

GOLDEN = load_golden(load_eval_config().golden_path)
CATEGORY = {(i.question, i.asked_as): i.category for i in GOLDEN}


def meta():
    cfg = load_config()
    return build_meta(read_manifest(cfg.manifest_path), GOLDEN, cfg.roles)


def test_finance_examples_show_filings_and_spreadsheets_first():
    own = meta()["examples"]["by_role"]["finance"]["own_team"]
    cats = [CATEGORY[(q, "finance")] for q in own]
    assert cats[:3] == ["cross_source_finance", "sec_lookup", "spreadsheet_lookup"]


def test_examples_vary_category_and_every_role_has_some():
    by_role = meta()["examples"]["by_role"]
    for role, groups in by_role.items():
        assert groups["own_team"], role
        cats = [CATEGORY[(q, role)] for q in groups["own_team"]]
        assert len(cats) == len(groups["own_team"])
