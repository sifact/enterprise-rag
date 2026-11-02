"""Static facts for the UI: roles, what each can see, and example questions per role.

Examples come from the reviewed golden set, so every suggested question has a known answer
(or a known reason to be refused).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from enterprise_rag.data import DocumentRecord
from enterprise_rag.evaluation import GoldenItem

ROLE_INFO = {
    "engineering": ("Engineering", "Engineering handbook pages"),
    "hr": ("People (HR)", "People, hiring, benefits and policy pages"),
    "marketing": ("Marketing", "Marketing handbook pages"),
    "legal": ("Legal", "Legal handbook pages and contract terms"),
    "sales": ("Sales", "Sales handbook pages and playbooks"),
    "finance": ("Finance", "Finance pages, SEC filings and budget spreadsheets"),
    "c_level": ("Executive (c_level)", "Everything in the company"),
}
OWN_TEAM = ("single_fact", "multi_hop", "sec_lookup", "spreadsheet_lookup",
            "cross_source_finance", "c_level")
SOURCE_LABELS = {"handbook": "GitLab handbook pages", "sec": "SEC filings (10-K, 10-Q)",
                 "synthetic": "Finance spreadsheets (fictional)"}


def build_meta(manifest: Sequence[DocumentRecord], golden: Sequence[GoldenItem],
               roles: Sequence[str], per_role: int = 3) -> dict:
    visible = Counter(r for rec in manifest for r in rec.allowed_roles)
    by_role = {}
    for role in roles:
        own = [i.question for i in golden if i.asked_as == role and i.category in OWN_TEAM]
        other = [i.question for i in golden if i.asked_as == role and i.category == "cross_role"]
        by_role[role] = {"own_team": own[:per_role], "other_team": other[:2]}
    attacks = (
        [{"question": i.question, "role": i.asked_as, "kind": "direct_injection"}
         for i in golden if i.category == "direct_injection"][:3]
        + [{"question": i.question, "role": i.asked_as, "kind": "indirect_injection"}
           for i in golden if i.category == "indirect_injection"][:2]
        + [{"question": i.question, "role": i.asked_as, "kind": "out_of_scope"}
           for i in golden if i.category == "out_of_scope"][:2]
    )
    return {
        "roles": [{"name": r, "label": ROLE_INFO.get(r, (r, ""))[0],
                   "description": ROLE_INFO.get(r, ("", ""))[1], "documents": visible[r]}
                  for r in roles],
        "examples": {"by_role": by_role, "attacks": attacks},
        "corpus": {"documents": len(manifest),
                   "sources": [{"label": SOURCE_LABELS.get(s, s), "documents": n}
                               for s, n in sorted(Counter(r.source for r in manifest).items())]},
    }
