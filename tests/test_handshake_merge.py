import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "reconcile_merge.py"
HELLO = ROOT / "_report" / "reconciliation" / "hello.json"
HELLO_ALT = ROOT / "_report" / "reconciliation" / "hello-alt.json"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, cwd=ROOT)


def test_merge_summary_detects_differences(tmp_path):
    out = tmp_path / "summary.json"
    result = run(str(HELLO), str(HELLO_ALT), "--output", str(out))
    assert result.returncode == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["matches"] is False
    assert payload["differences"], "expected differences"


def test_merge_summary_when_equal(tmp_path):
    copied = tmp_path / "hello.json"
    copied.write_text(HELLO.read_text(encoding="utf-8"), encoding="utf-8")
    result = run(str(HELLO), str(copied))
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["matches"] is True
    assert "safe to append" in payload["anchor_note"].lower()
