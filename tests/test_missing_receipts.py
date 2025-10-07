from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.planner import missing_receipts


def _write_plan(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_load_missing_filters_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plans_dir = tmp_path / "_plans"
    plans_dir.mkdir()
    _write_plan(
        plans_dir / "has-receipts.plan.json",
        {
            "plan_id": "HAS",
            "status": "queued",
            "receipts": ["docs/example.md"],
        },
    )
    _write_plan(
        plans_dir / "missing.plan.json",
        {
            "plan_id": "MISS",
            "status": "queued",
        },
    )
    _write_plan(
        plans_dir / "done.plan.json",
        {
            "plan_id": "DONE",
            "status": "done",
        },
    )
    monkeypatch.setattr(missing_receipts, "PLANS_DIR", plans_dir)

    rows = missing_receipts.load_missing({"queued"})
    assert len(rows) == 1
    assert rows[0]["plan_id"] == "MISS"

    rows_all = missing_receipts.load_missing({"queued", "done"})
    assert any(row["plan_id"] == "DONE" for row in rows_all)


def test_cli_table_output(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    plans_dir = tmp_path / "_plans"
    plans_dir.mkdir()
    _write_plan(
        plans_dir / "missing.plan.json",
        {
            "plan_id": "MISS",
            "status": "queued",
        },
    )
    monkeypatch.setattr(missing_receipts, "PLANS_DIR", plans_dir)

    exit_code = missing_receipts.main([])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "MISS" in captured.out
