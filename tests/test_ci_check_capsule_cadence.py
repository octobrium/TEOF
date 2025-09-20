import json
from importlib import reload
from pathlib import Path

import pytest

import scripts.ci.check_capsule_cadence as check_capsule


@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    root = tmp_path
    report_dir = root / "_report" / "capsule"
    report_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(check_capsule, "ROOT", root)
    reload(check_capsule)
    monkeypatch.setattr(check_capsule, "ROOT", root)
    check_capsule.SUMMARY_PATH = report_dir / "summary-latest.json"
    return report_dir


def test_missing_summary(tmp_repo):
    rc = check_capsule.main()
    assert rc == 1


def test_missing_receipt(tmp_repo):
    data = {
        "required_receipts": ["capsule/README.md"],
        "consensus_summary": "_report/consensus/summary-latest.json"
    }
    (tmp_repo / "summary-latest.json").write_text(json.dumps(data), encoding="utf-8")

    rc = check_capsule.main()
    assert rc == 1  # capsule/README.md missing in tmp repo


def test_success(tmp_repo):
    # Create fake receipts
    root = check_capsule.ROOT
    (root / "capsule").mkdir(parents=True, exist_ok=True)
    (root / "capsule" / "README.md").write_text("capsule", encoding="utf-8")
    (root / "capsule" / "current").mkdir(parents=True, exist_ok=True)
    (root / "capsule" / "current" / "hashes.json").write_text("{}", encoding="utf-8")
    (root / "governance").mkdir(parents=True, exist_ok=True)
    (root / "governance" / "anchors.json").write_text("[]", encoding="utf-8")
    (root / "_report" / "consensus").mkdir(parents=True, exist_ok=True)
    (root / "_report" / "consensus" / "summary-latest.json").write_text("{}", encoding="utf-8")

    data = {
        "required_receipts": [
            "capsule/README.md",
            "capsule/current/hashes.json",
            "governance/anchors.json"
        ],
        "consensus_summary": "_report/consensus/summary-latest.json"
    }
    (tmp_repo / "summary-latest.json").write_text(json.dumps(data), encoding="utf-8")

    rc = check_capsule.main()
    assert rc == 0
