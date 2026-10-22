# synthetic.py

Generates the fictional budget, headcount and vendor-spend workbooks for the finance role.

- Draws everything from one NumPy RNG seeded from the config, in a fixed order, so the output depends only on the seed.
- Models quarter-end headcount per department, region and level: Q1-Q2 are actuals, Q3-Q4 are plan (GitLab FY2027).
- Derives budgeted salaries from that headcount (heads × loaded cost / 4), so the workbooks agree and cross-file questions have exact answers.
- Adds other opex lines, actual-vs-plan variance and a fictional vendor list with plan and H1 actuals.
- Writes an `About` sheet in every workbook marking the data as fictional, and emits finance-only `DocumentRecord`s.
