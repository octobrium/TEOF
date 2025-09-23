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

    status = objectives_status.compute_status(window_days=7)
    assert status["objectives"]["O1"]["reflections_last_window"] == 1
    assert status["objectives"]["O1"]["meets_target"] is True
    assert status["objectives"]["O2"]["autonomy_cycles_last_window"] == 1
    assert status["objectives"]["O5"]["meets_minimum"] is True
    assert status["objectives"]["O7"]["meets_target"] is True


def test_compute_status_missing_files(status_root: Path) -> None:
    status = objectives_status.compute_status(window_days=7)
    assert status["objectives"]["O1"]["reflections_last_window"] == 0
    assert status["objectives"]["O2"]["autonomy_cycles_last_window"] == 0
    assert status["objectives"]["O5"] is None
    assert status["objectives"]["O7"]["meets_target"] is False
