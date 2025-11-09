from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.agent import confidence_calibration as cc


def _write_plan(path: Path, plan_id: str, status: str) -> None:
    payload = {
        "version": 0,
        "plan_id": plan_id,
        "created": "2025-10-01T00:00:00Z",
        "actor": "tester",
        "summary": "Test plan",
        "status": status,
        "layer": "L5",
        "systemic_scale": 5,
        "systemic_targets": ["S4", "S5"],
        "layer_targets": ["L5"],
        "steps": [
            {"id": "S1", "title": "Do thing", "status": "done", "notes": "", "receipts": []},
        ],
        "checkpoint": {"description": "done", "owner": "tester", "status": "pending"},
        "receipts": [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_confidence_log(path: Path, entries: list[dict]) -> None:
    text = "\n".join(json.dumps(entry) for entry in entries) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_collect_aggregates_records(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    base = repo / "_report" / "agent" / "codex-test"
    _write_confidence_log(
        base / "confidence.jsonl",
        [
            {"ts": "2025-10-01T00:00:00Z", "agent": "codex-test", "confidence": 0.8, "note": "plan:2025-10-01-alpha"},
            {"ts": "2025-10-02T00:00:00Z", "agent": "codex-test", "confidence": 0.9},
        ],
    )
    monkeypatch.setattr(cc, "ROOT", repo)
    out_path = repo / "artifacts" / "confidence_calibration" / "latest.json"
    rc = cc.main(["collect", "--base-dir", str(base.parent), "--out", str(out_path)])
    assert rc == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["count"] == 2
    assert payload["records"][0]["plan_id"] == "2025-10-01-alpha"


def test_aggregate_computes_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    records_path = repo / "artifacts" / "confidence_calibration" / "latest.json"
    records_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": "2025-10-02T00:00:00Z",
        "records": [
            {"ts": "2025-10-01T00:00:00Z", "agent": "codex-test", "confidence": 0.8, "plan_id": "2025-10-01-alpha"},
            {"ts": "2025-10-02T00:00:00Z", "agent": "codex-test", "confidence": 0.2, "plan_id": "2025-10-02-beta"},
        ],
    }
    records_path.write_text(json.dumps(payload), encoding="utf-8")
    plans_dir = repo / "_plans"
    plans_dir.mkdir(parents=True)
    _write_plan(plans_dir / "2025-10-01-alpha.plan.json", "2025-10-01-alpha", "done")
    _write_plan(plans_dir / "2025-10-02-beta.plan.json", "2025-10-02-beta", "in_progress")
    monkeypatch.setattr(cc, "ROOT", repo)
    report_dir = repo / "_report" / "usage" / "confidence-calibration"
    rc = cc.main(
        [
            "aggregate",
            "--source",
            str(records_path),
            "--plans-dir",
            str(plans_dir),
            "--report-dir",
            str(report_dir),
            "--window",
            "10",
            "--delta-threshold",
            "0.1",
        ]
    )
    assert rc == 0
    summary_files = sorted(report_dir.glob("summary-*.json"))
    assert summary_files, "summary not written"
    summary = json.loads(summary_files[-1].read_text(encoding="utf-8"))
    assert summary["agents"][0]["samples"] == 2
    assert summary["agents"][0]["alerts"], "expected alert because mean delta crosses threshold"


def test_alerts_emits_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    summary_path = repo / "_report" / "usage" / "confidence-calibration" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_payload = {
        "generated_at": "2025-10-02T00:00:00Z",
        "window": 20,
        "delta_threshold": 0.15,
        "agents": [
            {
                "agent": "codex-test",
                "samples": 3,
                "window_samples": 3,
                "mean_delta": 0.2,
                "mean_abs_delta": 0.2,
                "brier_score": 0.05,
                "overconfidence_rate": 0.5,
                "underconfidence_rate": 0.0,
                "latest": {"ts": "2025-10-02T00:00:00Z", "plan_id": "2025-10-01-alpha", "confidence": 0.8},
                "alerts": ["mean_delta"],
            }
        ],
        "alerts": ["codex-test"],
    }
    summary_path.write_text(json.dumps(summary_payload), encoding="utf-8")
    monkeypatch.setattr(cc, "ROOT", repo)
    rc = cc.main(
        [
            "alerts",
            "--summary",
            str(summary_path),
            "--report-dir",
            str(summary_path.parent),
            "--mean-delta-limit",
            "0.15",
            "--overconfidence-limit",
            "0.3",
        ]
    )
    assert rc == 1
    alerts_files = list(summary_path.parent.glob("alerts-*.json"))
    assert alerts_files
    alerts = json.loads(alerts_files[-1].read_text(encoding="utf-8"))
    assert alerts["alerts"][0]["agent"] == "codex-test"
