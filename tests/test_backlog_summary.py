from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.planner import backlog_summary


def _write_plan(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_summarise_counts_and_pending(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plans_dir = tmp_path / "_plans"
    plans_dir.mkdir()
    _write_plan(
        plans_dir / "plan-one.plan.json",
        {
            "plan_id": "PLAN-ONE",
            "status": "queued",
            "priority": 1,
            "layer": "L4",
            "systemic_scale": 6,
            "summary": "First plan",
        },
    )
    _write_plan(
        plans_dir / "plan-two.plan.json",
        {
            "plan_id": "PLAN-TWO",
            "status": "done",
            "priority": 3,
        },
    )
    _write_plan(
        plans_dir / "plan-three.plan.json",
        {
            "plan_id": "PLAN-THREE",
            "status": "in_progress",
            "priority": 0,
            "layer": "L2",
            "systemic_scale": 4,
            "summary": "Urgent plan",
        },
    )

    monkeypatch.setattr(backlog_summary, "PLANS_DIR", plans_dir)

    entries = list(backlog_summary.load_plans())
    summary = backlog_summary.summarise(entries)

    assert summary["total"] == 3
    assert summary["status_counts"]["done"] == 1
    pending = summary["pending"]
    assert [entry.plan_id for entry in pending] == ["PLAN-THREE", "PLAN-ONE"]


def test_cli_json_output(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    plans_dir = tmp_path / "_plans"
    plans_dir.mkdir()
    _write_plan(
        plans_dir / "plan-one.plan.json",
        {
            "plan_id": "PLAN-ONE",
            "status": "queued",
            "priority": 2,
        },
    )
    monkeypatch.setattr(backlog_summary, "PLANS_DIR", plans_dir)

    exit_code = backlog_summary.main(["--format", "json"])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["total"] == 1
    assert payload["status_counts"]["queued"] == 1
    assert payload["pending"][0]["plan_id"] == "PLAN-ONE"
