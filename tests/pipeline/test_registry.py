import pytest

from enterprise_rag.config import load_config, load_eval_config, load_rag_config
from enterprise_rag.pipeline import PIPELINE_NAMES, build_pipeline, collection_name


def test_unknown_pipeline_name_raises():
    with pytest.raises(ValueError, match="Unknown pipeline"):
        build_pipeline("nope", load_config(), load_rag_config(), load_eval_config(), False)


def test_safety_runs_use_the_collection_with_fixtures():
    rag = load_rag_config()
    assert collection_name(rag, safety=True) == rag.collection + "_safety"
    assert collection_name(rag, safety=False) == rag.collection
    assert {"reference-bm25", "hybrid", "hybrid-rerank"} <= set(PIPELINE_NAMES)
