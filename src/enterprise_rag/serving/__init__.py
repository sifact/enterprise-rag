"""The web API and static UI hosting for the demo."""

from enterprise_rag.serving.app import create_app
from enterprise_rag.serving.results import load_results

_LAZY = {"build_meta": "enterprise_rag.serving.examples"}

__all__ = ["build_meta", "create_app", "load_results"]


def __getattr__(name: str):
    """Heavy members load on first use, so the serverless API only imports what it needs."""
    if name in _LAZY:
        import importlib

        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
