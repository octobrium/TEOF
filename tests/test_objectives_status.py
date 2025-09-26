from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tools.autonomy import objectives_status


@pytest.fixture()
def status_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path
    monkeypatch.setattr(objectives_status, "ROOT", root)
    monkeypatch.setattr(objectives_status, "REFLECTION_DIR", root / "memory" / "reflections")
    monkeypatch.setattr(objectives_status, "CONDUCTOR_DIR", root / "_report" / "usage" / "autonomy-conductor")
    monkeypatch.setattr(objectives_status, "AUTONOMY_ACTIONS_DIR", root / "_report" / "usage" / "autonomy-actions")
    monkeypatch.setattr(objectives_status, "AUTH_PATH_JSON", root / "_report" / "usage" / "external-authenticity.json")
    monkeypatch.setattr(objectives_status, "EXTERNAL_SUMMARY", root / "_report" / "usage" / "external-summary.json")
    monkeypatch.setattr(objectives_status, "COORDINATION_AGENT_DIR", root / "_report" / "agent")
    monkeypatch.setattr(
        objectives_status,
        "COORDINATION_DOC_PATHS",
        (
            root / "docs" / "vision" / "multi-neuron-playbook.md",
            root / "docs" / "vision" / "properties-ledger.md",
            root / "docs" / "vision" / "objectives-ledger.md",
            root / "docs" / "quick-links.md",
        ),
    )
    monkeypatch.setattr(objectives_status, "IMPACT_LOG_PATH", root / "memory" / "impact" / "log.jsonl")
    monkeypatch.setattr(
        objectives_status, "IMPACT_LEDGER_PATH", root / "docs" / "vision" / "impact-ledger.md"
    )
    monkeypatch.setattr(objectives_status, "CLAIMS_DIR", root / "_bus" / "claims")
    return root


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_compute_status_basic(status_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    now = datetime.now(timezone.utc)
    # Reflection within window
    _write_json(
        objectives_status.REFLECTION_DIR / "reflection-demo.json",
        {"captured_at": (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")},
    )
    # Conductor receipt within window
    _write_json(
        objectives_status.CONDUCTOR_DIR / "conductor-demo.json",
        {"generated_at": (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")},
    )
    # Authenticity file
    _write_json(
        objectives_status.AUTH_PATH_JSON,
        {"overall_avg_trust": 0.8, "attention_feeds": []},
    )
    # External summary file
    external_path = objectives_status.EXTERNAL_SUMMARY
    external_path.parent.mkdir(parents=True, exist_ok=True)
    external_path.write_text("{}", encoding="utf-8")

    # Coordination docs and dashboard receipt
    for doc_path in objectives_status.COORDINATION_DOC_PATHS:
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text("coord doc", encoding="utf-8")
    dashboard = objectives_status.COORDINATION_AGENT_DIR / "codex-1" / "apoptosis-009" / "dashboard-sample.md"
    dashboard.parent.mkdir(parents=True, exist_ok=True)
    dashboard.write_text("dash", encoding="utf-8")

    # Impact log + ledger summary
    impact_log = objectives_status.IMPACT_LOG_PATH
    impact_log.parent.mkdir(parents=True, exist_ok=True)
    impact_log.write_text(
        json.dumps(
            {
                "recorded_at": (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "title": "Pilot",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    impact_ledger = objectives_status.IMPACT_LEDGER_PATH
    impact_ledger.parent.mkdir(parents=True, exist_ok=True)
    impact_ledger.write_text("- *2025-09-23 — Example*\n", encoding="utf-8")

    # Cooperative cadence: two agents claimed tasks
    claims_dir = objectives_status.CLAIMS_DIR
    for idx, agent in enumerate(("codex-3", "codex-4"), start=1):
        _write_json(
            claims_dir / f"QUEUE-0{idx}.json",
            {
                "agent_id": agent,
                "claimed_at": (now - timedelta(days=idx)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )

    status = objectives_status.compute_status(window_days=7)
    assert status["objectives"]["O1"]["reflections_last_window"] == 1
    assert status["objectives"]["O1"]["meets_target"] is True
    assert status["objectives"]["O2"]["autonomy_cycles_last_window"] == 1
    assert status["objectives"]["O3"]["meets_target"] is True
    assert status["objectives"]["O4"]["impact_entries_last_window"] == 1
    assert status["objectives"]["O4"]["meets_target"] is True
    assert status["objectives"]["O5"]["meets_minimum"] is True
    assert status["objectives"]["O6"]["unique_agents_last_window"] == 2
    assert status["objectives"]["O6"]["meets_target"] is True
    assert status["objectives"]["O7"]["meets_target"] is True


def test_compute_status_missing_files(status_root: Path) -> None:
    status = objectives_status.compute_status(window_days=7)
    assert status["objectives"]["O1"]["reflections_last_window"] == 0
    assert status["objectives"]["O2"]["autonomy_cycles_last_window"] == 0
    assert status["objectives"]["O5"] is None
    assert status["objectives"]["O3"]["meets_target"] is False
    assert status["objectives"]["O3"]["missing_docs"]
    assert status["objectives"]["O4"]["impact_entries_last_window"] == 0
    assert status["objectives"]["O4"]["meets_target"] is False
    assert status["objectives"]["O6"]["unique_agents_last_window"] == 0
    assert status["objectives"]["O6"]["meets_target"] is False
    assert status["objectives"]["O7"]["meets_target"] is False
