from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.agent import autonomy_status


def write_hygiene(path: Path, **fields) -> None:
    data = {
        "generated_at": "2025-09-21T12:00:00Z",
        "metrics": {
            "plans_total": 10,
            "plans_missing_receipts": 1,
            "missing_plan_ids": ["plan-a"],
            "slow_plans": [["plan-b", 123.0, None]],
        },
    }
    data.update(fields)
    path.write_text(json.dumps(data), encoding="utf-8")


def write_batch(path: Path, summary: str) -> None:
    payload = {
        "generated_at": "20250921T181427Z",
        "agent": "codex-1",
        "operator_preset": {"summary": summary},
        "receipts_hygiene": {"metrics": {"plans_missing_receipts": 0, "slow_plans": []}},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_autonomy_status_summary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    hygiene = tmp_path / "_report" / "usage" / "receipts-hygiene-summary.json"
    hygiene.parent.mkdir(parents=True, exist_ok=True)
    write_hygiene(hygiene)

    batch_dir = tmp_path / "_report" / "usage" / "batch-refinement"
    batch_dir.mkdir(parents=True, exist_ok=True)
    write_batch(batch_dir / "batch-refinement-1.json", "pass")
    write_batch(batch_dir / "batch-refinement-2.json", "warn")

    macro_payload = {"status": "ready", "summary": {"ready": 4, "attention": 0, "total": 4}}

    monkeypatch.setattr(autonomy_status, "HYGIENE_SUMMARY", hygiene)
    monkeypatch.setattr(autonomy_status, "BATCH_DIR", batch_dir)
    monkeypatch.setattr(autonomy_status, "ROOT", tmp_path)
    monkeypatch.setattr(
        autonomy_status,
        "load_macro_hygiene",
        lambda *, write_receipt: macro_payload,
    )
    monkeypatch.setattr(
        autonomy_status.receipt_brief,
        "generate_plan_brief",
        lambda plan_id: f"{plan_id} brief text",
    )

    summary = autonomy_status.summarise(
        autonomy_status.load_hygiene(),
        autonomy_status.load_batch_logs(),
        macro_payload,
    )
    assert summary["hygiene"]["plans_missing_receipts"] == 1
    assert summary["batch_logs"]["warn_count"] == 1
    assert summary["macro_hygiene"] == macro_payload
    assert summary["plan_briefs"] == {
        "plan-a": "plan-a brief text",
        "plan-b": "plan-b brief text",
    }

    exit_code = autonomy_status.main(["--json", "--limit", "1"])
    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["batch_logs"]["entries"] == 1
    receipt_path = tmp_path / "_report" / "usage" / "autonomy-status.json"
    assert receipt_path.exists()
