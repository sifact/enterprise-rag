from dataclasses import replace

import pytest

from enterprise_rag.config import load_config


@pytest.fixture
def cfg(tmp_path):
    """Real config, with outputs redirected to a temp dir."""
    return replace(load_config(), raw_dir=tmp_path / "raw", cache_dir=tmp_path / "cache")


class FakeEmbedders:
    """Deterministic stand-in for the fastembed models: bag-of-words hashing, no downloads."""

    dense_dim = 32

    @staticmethod
    def _words(text):
        return [w.strip(".,?!").lower() for w in text.split() if w.strip(".,?!")]

    def _vec(self, text):
        v = [0.0] * self.dense_dim
        for w in self._words(text):
            v[hash(w) % self.dense_dim] += 1.0
        return v if any(v) else [1.0] + [0.0] * (self.dense_dim - 1)

    def dense(self, texts):
        return [self._vec(t) for t in texts]

    def dense_query(self, text):
        return self._vec(text)

    def sparse(self, texts):
        from enterprise_rag.indexing import SparseVec

        out = []
        for t in texts:
            counts = {}
            for w in self._words(t):
                counts[abs(hash(w)) % 100_000] = counts.get(abs(hash(w)) % 100_000, 0) + 1.0
            out.append(SparseVec(sorted(counts), [counts[i] for i in sorted(counts)]))
        return out

    def sparse_query(self, text):
        return self.sparse([text])[0]

    def rerank(self, query, texts):
        q = set(self._words(query))
        return [float(len(q & set(self._words(t)))) for t in texts]


@pytest.fixture
def fake_embedders():
    return FakeEmbedders()
