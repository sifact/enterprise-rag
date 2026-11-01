# computed.py

Builds the 8 finance items whose gold answers are computed with pandas instead of drafted.

- It regenerates the synthetic workbooks with `build_workbooks` (same seed, same numbers) and round-trips them through Excel so the values and dtypes match the files on disk.
- Six `spreadsheet_lookup` items (`fin-xlsx-001..006`) cover a budget variance, a quarterly plan, a full-year department plan, planned hires and two vendor amounts.
- Two `cross_source_finance` items (`fin-cross-001..002`) combine two sheets: a vendor's plan or actuals as a percentage of its department's budget.
- Each evidence quote is the matching row's CSV line exactly as `sheet_to_text` renders the sheet, widened with neighbouring rows until it reaches the 10-word minimum.
- Questions are templated in plain language; every item is asked by `finance` and carries a `NumericAnswer` so it's scored by exact numeric match.
