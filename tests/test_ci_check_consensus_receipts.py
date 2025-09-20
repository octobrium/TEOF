import json
from importlib import reload
from pathlib import Path

import pytest

import scripts.ci.check_consensus_receipts as check_consensus


@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    root = tmp_path
    report_dir = root / "_report" / "consensus"
    report_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(check_consensus, "ROOT", root)
    reload(check_consensus)
    monkeypatch.setattr(check_consensus, "ROOT", root)
    check_consensus.SUMMARY_PATH = report_dir / "summary-latest.json"
    return report_dir


def test_missing_summary(tmp_repo):
    rc = check_consensus.main()
    assert rc == 1


def test_missing_receipt(tmp_repo):
    summary = {
        "tasks": [
            {
                "task_id": "QUEUE-999",
                "required_receipts": ["_report/consensus/missing.json"],
            }
        ]
    }
    (tmp_repo / "summary-latest.json").write_text(
        json.dumps(summary) + "\n", encoding="utf-8"
    )

    rc = check_consensus.main()
    assert rc == 1


def test_success(tmp_repo):
    receipt_path = tmp_repo / "ci-ledger.jsonl"
    receipt_path.write_text("{}\n", encoding="utf-8")
    summary = {
        "tasks": [
            {
                "task_id": "QUEUE-030",
                "required_receipts": [
                    str(Path("_report/consensus/ci-ledger.jsonl"))
                ],
            }
        ]
    }
    (tmp_repo / "summary-latest.json").write_text(
        json.dumps(summary) + "\n", encoding="utf-8"
    )

    rc = check_consensus.main()
    assert rc == 0
