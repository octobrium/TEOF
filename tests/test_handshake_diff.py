import json
import subprocess
import sys
from pathlib import Path

def run(*args):
    return subprocess.run(args, capture_output=True, text=True, cwd=Path(__file__).resolve().parents[1])

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "reconcile_diff.py"
HELLO = Path(__file__).resolve().parents[1] / "_report" / "reconciliation" / "hello.json"
HELLO_ALT = Path(__file__).resolve().parents[1] / "_report" / "reconciliation" / "hello-alt.json"


def test_diff_detects_changes():
    result = run(sys.executable, str(SCRIPT), str(HELLO), str(HELLO_ALT))
    assert result.returncode == 1
    assert "differences detected" in result.stdout


def test_diff_success_when_equal(tmp_path):
    copied = tmp_path / "hello.json"
    copied.write_text(HELLO.read_text(encoding="utf-8"), encoding="utf-8")
    result = run(sys.executable, str(SCRIPT), str(HELLO), str(copied))
    assert result.returncode == 0
    assert "match" in result.stdout
