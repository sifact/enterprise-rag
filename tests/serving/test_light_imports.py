import subprocess
import sys

# Not installed on the serverless host (see requirements.txt): the API must import without them.
HEAVY = ("pandas", "fastembed", "onnxruntime", "deepeval", "rapidfuzz", "openpyxl", "playwright",
         "pypdf", "rank_bm25")
ENTRY = ("enterprise_rag.serving.app", "enterprise_rag.pipeline.rag",
         "enterprise_rag.retrieval.types", "enterprise_rag.serving.cloud_app")


def test_serving_imports_work_without_heavy_packages():
    blocked = list(HEAVY)
    code = ("import sys\n"
            + "".join(f"sys.modules[{m!r}] = None\n" for m in blocked)  # import now fails
            + "".join(f"import {m}\n" for m in ENTRY) + "print('ok')")
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                            check=False)
    assert result.stdout.strip() == "ok", result.stderr[-800:]
