import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "runner" / "run.py"
TEST_RECEIPT_ROOT = ROOT / "_report" / "runner_test"


def run_runner(tmp_path, *args):
    receipt_dir = TEST_RECEIPT_ROOT / tmp_path.name
    cmd = [
        sys.executable,
        str(RUNNER),
        "--receipt-dir",
        str(receipt_dir),
        *args,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)


def read_receipt(tmp_path: Path) -> dict:
    receipt_dir = TEST_RECEIPT_ROOT / tmp_path.name
    receipts = sorted(receipt_dir.glob("*.json"))
    assert receipts, "no receipt produced"
    return json.loads(receipts[-1].read_text(encoding="utf-8"))


def test_runner_executes_direct_command(tmp_path):
    result = run_runner(tmp_path, "--", "echo", "hello")
    assert result.returncode == 0
    assert "hello" in result.stdout

    receipt = read_receipt(tmp_path)
    assert receipt["shell"] is False
    assert receipt["command"] == ["echo", "hello"]
    assert receipt["exit_code"] == 0


def test_runner_shell_mode(tmp_path):
    shell_command = "echo 'shell' | tr a-z A-Z"
    result = run_runner(tmp_path, "--shell", "--", shell_command)
    assert result.returncode == 0
    assert "SHELL" in result.stdout

    receipt = read_receipt(tmp_path)
    assert receipt["shell"] is True
    assert receipt["command"] == shell_command
    assert receipt["exit_code"] == 0
