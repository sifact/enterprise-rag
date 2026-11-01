# golden.py

Defines a golden item, stores the set as JSONL, splits it into dev/test and validates it.

- `GoldenItem` holds the question, the asking role, the category, the expected behavior (`answer` or `refuse`), the reference answer, an optional `NumericAnswer` and verbatim `Evidence` quotes.
- `CATEGORIES` maps each of the 11 categories to its expected behavior; indirect-injection items are answered, just without following the planted instruction.
- `assign_splits` shuffles each category with the config seed and puts half (rounded down) in `dev`, the rest in `test`, so both splits cover every category.
- `validate_golden` checks roles, categories, quote length (10-60 words), that the asking role can see its own evidence, that a cross-role item's role can't see its forbidden docs, and that every quote still exists in its document.
- Errors are collected and raised together, each prefixed with the item ID, so a re-fetched corpus shows every broken item at once.
