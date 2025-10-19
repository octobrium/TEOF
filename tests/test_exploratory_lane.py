from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tools.planner import exploratory_lane


def _write_plan(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_scan_lane_counts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path
    plan_dir = root / "_plans" / "exploratory"
    expires_at = "2025-10-20T00:00:00Z"
    _write_plan(
        plan_dir / "2025-10-18-sandbox.plan.json",
        {
            "plan_id": "2025-10-18-sandbox",
            "status": "queued",
            "exploratory": {"expires_at": expires_at, "horizon_hours": 72},
        },
    )
    receipts_dir = root / "_report" / "exploratory" / "2025-10-18-sandbox"
    receipts_dir.mkdir(parents=True, exist_ok=True)
    (receipts_dir / "note.md").write_text("draft\n", encoding="utf-8")

    monkeypatch.setattr(exploratory_lane, "_now", lambda: datetime(2025, 10, 19, 0, 0, tzinfo=timezone.utc))

    summary = exploratory_lane.scan_lane(root=root, warning_hours=36.0)
    assert summary["counts"]["total"] == 1
    assert summary["counts"]["expired"] == 0
    assert summary["counts"]["expiring"] == 1
    assert summary["counts"]["receipts_missing"] == 0
    assert summary["plans"][0]["receipts_count"] == 1
    assert summary["plans"][0]["expires_at"] == expires_at


def test_cli_outputs_table(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path
    plan_dir = root / "_plans" / "exploratory"
    _write_plan(
        plan_dir / "2025-10-18-sandbox.plan.json",
        {
            "plan_id": "2025-10-18-sandbox",
            "status": "queued",
            "exploratory": {"expires_at": "2025-10-20T00:00:00Z", "horizon_hours": 72},
        },
    )
    monkeypatch.setattr(exploratory_lane, "ROOT", root)
    monkeypatch.setattr(exploratory_lane, "_now", lambda: datetime(2025, 10, 19, 0, 0, tzinfo=timezone.utc))
    monkeypatch.setattr(
        exploratory_lane,
        "DEFAULT_RECEIPT_PATH",
        root / "_report" / "usage" / "exploratory-latest.json",
    )
    exit_code = exploratory_lane.main(
        [
            "--format",
            "table",
            "--receipt",
        ]
    )
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "plan_id" in output
    assert "2025-10-18-sandbox" in output
    receipt_path = root / "_report" / "usage" / "exploratory-latest.json"
    assert receipt_path.exists()
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert payload["counts"]["total"] == 1
