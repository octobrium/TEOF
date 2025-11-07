from __future__ import annotations

import subprocess
import json
from pathlib import Path
from types import SimpleNamespace

from teof.commands import up as up_cmd

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "bin" / "teof-eval-PROTOTYPE.sh"


def test_teof_eval_prototype_shell_syntax() -> None:
    """Ensure the Tier 1 prototype script stays bash-sane."""
    proc = subprocess.run(
        ["bash", "-n", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_teof_up_eval_writes_receipt(tmp_path: Path) -> None:
    """`teof up --eval` should record a Tier 1 receipt."""
    receipt_dir = tmp_path / "receipts"
    args = SimpleNamespace(
        eval=True,
        skip_install=True,
        receipt_dir=receipt_dir,
        _teof_up_parser=None,
    )
    rc = up_cmd.run(args)
    assert rc == 0
    receipts = sorted(receipt_dir.glob("tier1-evaluation-*.json"))
    assert receipts, "expected evaluation receipt"
    data = json.loads(receipts[-1].read_text(encoding="utf-8"))
    assert data["document_count"] == 10
