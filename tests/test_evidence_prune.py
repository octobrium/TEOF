from __future__ import annotations

import json
from pathlib import Path

from tools.agent import receipts_index
from tools.automation import evidence_prune
from tools.maintenance import evidence_usage


def _configure_modules(monkeypatch, root: Path) -> None:
    monkeypatch.setattr(receipts_index, "ROOT", root)
    monkeypatch.setattr(receipts_index, "PLANS_DIR", root / "_plans")
    monkeypatch.setattr(receipts_index, "REPORT_DIR", root / "_report")
    monkeypatch.setattr(receipts_index, "MANAGER_REPORT", root / "_bus" / "messages" / "manager-report.jsonl")
    monkeypatch.setattr(receipts_index, "DEFAULT_USAGE_DIR", root / "_report" / "usage")
    monkeypatch.setattr(evidence_usage, "ROOT", root)
    monkeypatch.setattr(evidence_usage, "DEFAULT_OUTPUT", root / "_report" / "usage" / "evidence-usage.json")


def _make_repo(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "repo"
    (root / "_plans").mkdir(parents=True, exist_ok=True)
    (root / "_report" / "usage" / "keep").mkdir(parents=True, exist_ok=True)
    (root / "_bus" / "messages").mkdir(parents=True, exist_ok=True)
    kept_receipt = root / "_report" / "usage" / "keep" / "keep.json"
    kept_receipt.write_text("{}", encoding="utf-8")
    plan = {
        "plan_id": "demo-plan",
        "steps": [],
        "receipts": [
            "_report/usage/keep/keep.json",
        ],
    }
    (root / "_plans" / "demo-plan.plan.json").write_text(json.dumps(plan), encoding="utf-8")
    orphan_dir = root / "_report" / "usage" / "stale"
    orphan_dir.mkdir(parents=True, exist_ok=True)
    orphan_file = orphan_dir / "orphan.json"
    orphan_file.write_text("{}", encoding="utf-8")
    _configure_modules(monkeypatch, root)
    return root


def test_run_creates_receipts_and_prunes(tmp_path: Path, monkeypatch) -> None:
    root = _make_repo(tmp_path, monkeypatch)
    out_dir = Path("_report/usage/evidence-prune")
    args = [
        "run",
        "--root",
        str(root),
        "--out",
        str(out_dir),
        "--cutoff-hours",
        "0.0",
        "--apply-prune",
    ]
    rc = evidence_prune.main(args)
    assert rc == 0
    receipt_dir = (root / out_dir)
    pointer_path = receipt_dir / "latest.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    evidence_path = root / pointer["evidence_receipt"]
    prune_path = root / pointer["prune"]["receipt"]
    assert evidence_path.exists()
    assert prune_path.exists()
    assert pointer["orphan_receipts"] >= 1
    assert pointer["prune"]["applied"] is True
    # orphan should be moved to _apoptosis
    apoptosis = next((root / "_apoptosis").rglob("orphan.json"), None)
    assert apoptosis is not None


def test_guard_fails_when_pointer_stale(tmp_path: Path, monkeypatch) -> None:
    root = _make_repo(tmp_path, monkeypatch)
    out_dir = Path("_report/usage/evidence-prune")
    evidence_prune.main(
        [
            "run",
            "--root",
            str(root),
            "--out",
            str(out_dir),
            "--apply-prune",
            "--cutoff-hours",
            "0.0",
        ]
    )
    pointer_path = root / out_dir / "latest.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    pointer["generated_at"] = "2020-01-01T00:00:00Z"
    pointer_path.write_text(json.dumps(pointer), encoding="utf-8")

    rc = evidence_prune.main(
        [
            "guard",
            "--root",
            str(root),
            "--out",
            str(out_dir),
            "--max-age-hours",
            "1",
        ]
    )
    assert rc == 1
