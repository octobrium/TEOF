from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

import pytest

from tools.autonomy import systemic_radar as radar


def test_build_payload_aggregates_signals(monkeypatch):
    baseline = {
        "axes": [
            {"axis": "S1", "window_days": 3, "threshold": 2},
            {"axis": "S2", "max_age_hours": 12},
            {"axis": "S3", "threshold": 4},
            {"axis": "S4"},
            {"axis": "S6", "threshold": 0.9},
        ]
    }

    signals = {
        "S1": radar.AxisSignal("S1", "L0", "ready", "memory ok", ["memory/log.jsonl"], metric=7, threshold=5),
        "S2": radar.AxisSignal("S2", "L6", "attention", "autonomy stale", ["_report/usage/autonomy-status.json"], metric=25.0, threshold=12.0),
        "S3": radar.AxisSignal("S3", "L5", "ready", "backlog good", ["_report/usage/backlog-health/sample.json"], metric=5, threshold=4),
        "S4": radar.AxisSignal("S4", "L4", "ready", "macro hygiene clean", [], None, None),
        "S6": radar.AxisSignal("S6", "L4", "ready", "plan coverage 0.95", [], metric=0.95, threshold=0.9),
    }

    monkeypatch.setattr(radar, "_memory_signal", lambda window_days, target: signals["S1"])
    monkeypatch.setattr(radar, "_autonomy_signal", lambda max_age_hours=None: signals["S2"])
    monkeypatch.setattr(radar, "_latest_backlog_receipt", lambda threshold=None: signals["S3"])
    monkeypatch.setattr(radar, "_macro_hygiene_signal", lambda: signals["S4"])
    monkeypatch.setattr(radar, "_plan_receipt_ratio", lambda threshold=0.8: signals["S6"])
    monkeypatch.setattr(radar, "utc_timestamp", lambda: "2025-11-08T23:00:00Z")

    args = SimpleNamespace(
        memory_window_days=7,
        memory_target=5,
        plan_receipt_threshold=0.8,
        baseline_config=Path("baseline"),
        output=None,
        markdown=None,
    )

    payload = radar.build_payload(args, baseline)

    assert payload["generated_at"] == "2025-11-08T23:00:00Z"
    assert payload["summary"] == {"ready": 4, "attention": 1, "breach": 0}
    axes = {axis["axis"]: axis for axis in payload["axes"]}
    assert axes["S2"]["status"] == "attention"
    assert axes["S3"]["detail"].startswith("backlog")
    assert axes["S1"]["receipts"] == ["memory/log.jsonl"]


def test_persist_and_markdown(tmp_path, monkeypatch):
    payload = {
        "generated_at": "2025-11-08T23:10:00Z",
        "summary": {"ready": 2, "attention": 0, "breach": 0},
        "axes": [
            {"axis": "S1", "layer": "L0", "status": "ready", "detail": "memory healthy", "receipts": [], "metric": 5, "threshold": 5},
            {"axis": "S2", "layer": "L6", "status": "ready", "detail": "autonomy fresh", "receipts": ["_report/usage/autonomy-status.json"], "metric": 1.0, "threshold": 24},
        ],
    }

    radar_dir = tmp_path / "radar"
    monkeypatch.setattr(radar, "RADAR_DIR", radar_dir)
    monkeypatch.setattr(radar, "ROOT", tmp_path)

    path = radar.persist_payload(payload, output=None)
    assert path.exists()
    assert path.parent == radar_dir
    assert path.name == "systemic-radar-20251108T231000Z.json"

    latest_link = radar_dir / "latest.json"
    assert latest_link.is_symlink()
    assert latest_link.readlink() == Path(path.name)

    markdown_path = tmp_path / "docs" / "reports" / "systemic-radar.md"
    markdown_path.parent.mkdir(parents=True)
    radar._write_markdown(payload, path, markdown_path)
    contents = markdown_path.read_text(encoding="utf-8")
    assert "Systemic Radar Summary" in contents
    assert "Receipt:" in contents
    rel_receipt = path.relative_to(tmp_path)
    assert str(rel_receipt) in contents
    assert "S1:L0" in contents
