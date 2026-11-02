# store.py

Builds the embedded Qdrant collection that search reads from.

- `open_client` opens Qdrant in embedded, on-disk mode at `data/index`, so no separate database server is needed; only one process can open it at a time.
- `build_index` drops and recreates the collection, so an index never mixes chunks from two chunker or model versions.
- Each point has a named `dense` vector (cosine) and a `bm25` sparse vector with Qdrant's IDF modifier, both computed from `context_header + text`.
- The payload holds the chunk's text, title, section, page, source URL and `allowed_roles`; the role field is what every search filters on.
- Point IDs are UUIDv5 hashes of the chunk ID, so the same chunk always gets the same ID.
