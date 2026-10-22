# sec.py

Downloads GitLab's 10-K and 10-Q from SEC EDGAR and renders each one to PDF.

- Builds archive URLs from the CIK, accession number and primary document name in the config.
- Requires `SEC_USER_AGENT` with a contact email (EDGAR's fair-access policy) and fails with a clear `FetchError` otherwise.
- Keeps the original inline-XBRL HTML and prints it to Letter-size PDF with headless Chromium, because ingestion targets PDFs.
- Is idempotent: existing HTML/PDF files are reused unless `--force` is passed.
- Emits one finance-only `DocumentRecord` per filing, pointing at the PDF.
