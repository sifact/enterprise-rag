# handbook_pages.py

Parses GitLab Handbook markdown pages and picks a reproducible sample per section.

- Splits Hugo front matter from the body and takes the page title from `title:`, falling back to the file name.
- Counts only prose words: Hugo shortcodes, HTML, comments and link URLs are removed first.
- Drops stub pages below `min_words`. Pages that are mostly links make poor retrieval targets and poor golden-set sources.
- Samples each section with its own RNG seeded by `seed:section`, so resizing one section doesn't change another's pages.
- Maps a page path to its public URL (`a/_index.md` → `/handbook/a/`) for citations.
