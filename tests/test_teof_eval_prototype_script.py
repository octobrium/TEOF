from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

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


def test_teof_up_contribute_requires_id() -> None:
    args = SimpleNamespace(
        contribute=True,
        contributor_id=None,
        workload="tier1-eval",
        skip_install=True,
        receipt_dir=up_cmd.ONBOARDING_REPORT_DIR,
        eval=False,
        notes=None,
        _teof_up_parser=None,
    )
    with pytest.raises(SystemExit):
        up_cmd.run(args)


def test_teof_up_contribute_creates_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    contrib_root = tmp_path / "contributors"
    onboarding_dir = tmp_path / "onboarding"
    onboarding_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(up_cmd, "CONTRIBUTOR_ROOT", contrib_root)
    monkeypatch.setattr(up_cmd, "ONBOARDING_REPORT_DIR", onboarding_dir)

    args = SimpleNamespace(
        contribute=True,
        contributor_id="Test-Agent_01",
        workload="tier1-eval",
        skip_install=True,
        receipt_dir=onboarding_dir,
        eval=False,
        notes="unit-test",
        _teof_up_parser=None,
    )
    rc = up_cmd.run(args)
    assert rc == 0
    receipts = sorted(contrib_root.glob("test-agent_01/contribution-tier1-eval-*.json"))
    assert receipts, "expected contribution receipt"
    data = json.loads(receipts[-1].read_text(encoding="utf-8"))
    assert data["contributor_id"] == "test-agent_01"
