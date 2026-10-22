# manifest.py

Defines the per-document record and decides who can see each document.

- `DocumentRecord` holds the ID, path, title, source URL, department, license, content hash and `allowed_roles`.
- `allowed_roles_for` returns the owner role plus `c_level`, or every role for company-wide pages. It's the single place visibility is decided.
- Ingestion copies `allowed_roles` onto every chunk so the vector DB can pre-filter by role.
- `write_manifest` replaces only the rows of the sources being refreshed, so one source can be re-fetched alone.
- Rejects duplicate `doc_id`s and keeps rows sorted for stable diffs.
