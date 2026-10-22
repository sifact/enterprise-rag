# handbook.py

Fetches the pinned handbook commit and copies the sampled pages into the raw corpus.

- Does a shallow, blobless, sparse git checkout of only the configured folders' `.md` files at the pinned commit.
- Reuses the checkout under `data/cache/handbook` and only fetches again when HEAD isn't the pinned commit.
- Deletes `data/raw/handbook/` before copying, so a re-run never mixes pages from two different samples.
- Copies each sampled page to the same relative path under `data/raw/handbook/`.
- Emits one `DocumentRecord` per page with its section as department and `allowed_roles` from the section's role (or all roles for `general`).
