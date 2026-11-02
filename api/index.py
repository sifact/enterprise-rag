"""Vercel entry point: the FastAPI app served under /api/*.

The package isn't pip-installed on Vercel (that would pull the full dependency set), so its
source folder is put on the path directly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from enterprise_rag.serving.cloud_app import make_app

app = make_app()
