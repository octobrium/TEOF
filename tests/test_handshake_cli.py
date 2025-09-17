import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "reconcile_hello.py"


def run(*args):
    cmd = [sys.executable, str(SCRIPT), *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)


def test_emit_packet(tmp_path):
    receipts_dir = ROOT / "_report" / "runner"
    sample_receipt = next(receipts_dir.glob("*.json"))
    result = run(
        "test-instance",
        "--receipt",
        str(sample_receipt.relative_to(ROOT)),
        "--capability",
        "autocollab",
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["instance_id"] == "test-instance"
    assert payload["commandments_hash"]
    assert payload["anchors_hash"]
    assert payload["capabilities"] == ["autocollab"]
    assert payload["receipts"]["items"], "receipt list should not be empty"
