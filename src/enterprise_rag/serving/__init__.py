"""The web API and static UI hosting for the demo."""

from enterprise_rag.serving.app import create_app
from enterprise_rag.serving.examples import build_meta
from enterprise_rag.serving.results import load_results

__all__ = ["build_meta", "create_app", "load_results"]
