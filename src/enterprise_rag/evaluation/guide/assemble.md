# assemble.py

Merges reviewed drafts with computed and hand-written items, derives role twins and builds the frozen set.

- `parse_review_decisions` reads the ticked accept / edit / drop box and the review note for each item in the review file; `reviewed_drafts` keeps accepted and edited drafts and refuses to continue while any draft is undecided.
- `derive_cross_role` re-asks 12 department-owned questions as roles that can see none of their gold documents (never `c_level`, every other role at least once), with those documents as `forbidden_doc_ids` and a `twin: <id>` note for the answer-leak check.
- `derive_c_level` re-asks one question from each of 4 departments as `c_level`, which must still be answered.
- `assemble` merges all sources, adds the derived items, assigns the seeded dev/test split and runs `validate_golden` on the whole set, so a broken quote or role stops the freeze.
- `spot_check_ids` picks the random 20% sample the user reviews before `enterprise-rag build-golden` writes `eval/golden/v1.jsonl`.
