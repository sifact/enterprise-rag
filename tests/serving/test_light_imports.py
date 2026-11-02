import subprocess
import sys

HEAVY = ("pandas", "fastembed", "onnxruntime", "deepeval", "rapidfuzz", "openpyxl", "playwright",
         "pypdf", "rank_bm25")
ENTRY = ("enterprise_rag.serving.app", "enterprise_rag.pipeline.rag",
         "enterprise_rag.retrieval.types")


def test_serving_imports_stay_light():
    code = ("import sys\n" + "".join(f"import {m}\n" for m in ENTRY)
            + f"print(sorted(m for m in {HEAVY!r} if m in sys.modules))")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         check=True).stdout.strip()
    assert out == "[]", f"heavy modules imported by the serving path: {out}"
