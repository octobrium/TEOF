from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.network import convergence_metrics as cm


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_collect_and_aggregate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    recon_dir = repo / "_report" / "reconciliation"
    receipt_dir = repo / "_report" / "network" / "receipt_sync"
    plans_dir = repo / "_plans"
    audit_dir = repo / "_report" / "usage" / "autonomy-audit"

    _write_json(recon_dir / "sample.json", {"metrics": {"hash_match_rate": 0.96, "anchor_latency_minutes": 22}})
    _write_json(receipt_dir / "sync.json", {"gap_rate": 0.04})

    plan_payload = {
        "plan_id": "2025-11-09-sample",
        "steps": [
            {"id": "S1", "title": "Implement CMD-1 guard", "status": "done"},
            {"id": "S2", "title": "Document guard", "notes": "CMD-2 enforcement"},
            {"id": "S3", "title": "Regular step"},
        ],
    }
    _write_json(plans_dir / "2025-11-09-sample.plan.json", plan_payload)

    _write_json(audit_dir / "audit.json", {"correct": 9, "total": 10})

    monkeypatch.setattr(cm, "ROOT", repo)
    dataset_path = repo / "artifacts" / "convergence" / "records-latest.json"
    rc_collect = cm.main(
        [
            "collect",
            "--reconciliation",
            str(recon_dir),
            "--receipt-sync",
            str(receipt_dir),
            "--plans",
            str(plans_dir),
            "--autonomy-audit",
            str(audit_dir),
            "--out",
            str(dataset_path),
        ]
    )
    assert rc_collect == 0
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    assert dataset["reconciliation_rates"] == [0.96]
    assert dataset["receipt_gap_rates"] == [0.04]

    report_dir = repo / "_report" / "reconciliation" / "convergence-metrics"
    markdown_path = repo / "docs" / "reports" / "convergence-metrics.md"
    rc_aggregate = cm.main(
        [
            "aggregate",
            "--source",
            str(dataset_path),
            "--report-dir",
            str(report_dir),
            "--markdown",
            str(markdown_path),
            "--window-days",
            "14",
        ]
    )
    assert rc_aggregate == 0
    summary_files = sorted(report_dir.glob("convergence-*.json"))
    assert summary_files
    summary = json.loads(summary_files[-1].read_text(encoding="utf-8"))
    metrics = summary["metrics"]
    assert metrics["hash_match_rate"] == pytest.approx(0.96)
    assert metrics["receipt_gap_rate"] == pytest.approx(0.04)
    assert metrics["cmd_tag_ratio"] == pytest.approx(2 / 3)
    assert metrics["automation_accuracy"] == pytest.approx(0.9)
    assert markdown_path.read_text(encoding="utf-8").startswith("# Convergence Metrics")


def test_guard_flags_violations(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    summary = {
        "generated_at": "2025-11-09T06:25:00Z",
        "metrics": {
            "hash_match_rate": 0.90,
            "receipt_gap_rate": 0.1,
            "anchor_latency_minutes": 40,
            "cmd_tag_ratio": 0.5,
            "automation_accuracy": 0.7,
        },
    }
    summary_path = repo / "_report" / "reconciliation" / "convergence-metrics" / "convergence-test.json"
    _write_json(summary_path, summary)
    monkeypatch.setattr(cm, "ROOT", repo)
    rc = cm.main(
        [
            "guard",
            "--summary",
            str(summary_path),
            "--hash-min",
            "0.95",
            "--gap-max",
            "0.05",
            "--latency-max",
            "30",
            "--cmd-min",
            "0.8",
            "--automation-min",
            "0.9",
        ]
    )
    assert rc == 1
