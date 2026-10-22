from dataclasses import replace

import pytest

from enterprise_rag.config import load_config


@pytest.fixture
def cfg(tmp_path):
    """Real config, with outputs redirected to a temp dir."""
    return replace(load_config(), raw_dir=tmp_path / "raw", cache_dir=tmp_path / "cache")
