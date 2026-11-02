import json
import subprocess
import sys


def run_file(tmp_path, leak_rate, name="run.json"):
    path = tmp_path / name
    path.write_text(json.dumps({"aggregates": {"leak_rate": leak_rate, "n_items": 14}}))
    return path


def gate(*paths):
    return subprocess.run([sys.executable, "-m", "enterprise_rag.cli", "gate", *map(str, paths)],
                          capture_output=True, text=True, check=False)


def test_gate_fails_on_leak(tmp_path):
    result = gate(run_file(tmp_path, 0.1))
    assert result.returncode == 1 and "leak" in result.stdout.lower()


def test_gate_passes_without_leaks(tmp_path):
    assert gate(run_file(tmp_path, 0.0), run_file(tmp_path, 0.0, "b.json")).returncode == 0
