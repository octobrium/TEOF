from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.impact import bridge


def _write_plan(path: Path, *, plan_id: str, impact_ref: str | None) -> None:
    payload = {
        "version": 0,
        "plan_id": plan_id,
        "created": "2025-10-01T00:00:00Z",
        "actor": "tester",
        "summary": "Test plan",
        "status": "queued",
        "steps": [{"id": "S1", "title": "Do thing", "status": "queued", "notes": "", "receipts": []}],
        "checkpoint": {"description": "Ship impact bridge", "owner": "tester", "status": "pending"},
        "layer": "L4",
        "systemic_scale": 4,
        "systemic_targets": ["S4"],
        "layer_targets": ["L4"],
        "receipts": [],
        "links": [{"type": "queue", "ref": "queue/056-impact-bridge.md"}],
    }
    if impact_ref is not None:
        payload["impact_ref"] = impact_ref
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_bridge_generates_receipts_and_links(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path
    monkeypatch.setattr(bridge, "ROOT", repo)
    impact_dir = repo / "memory" / "impact"
    impact_dir.mkdir(parents=True)
    impact_log = impact_dir / "log.jsonl"
    impact_log.write_text(
        json.dumps(
            {
                "recorded_at": "2025-10-05T00:00:00Z",
                "title": "Relay insight outcome",
                "value": 1.0,
                "currency": "USD",
                "receipts": ["_report/usage/case-study/example.json"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    plans_dir = repo / "_plans"
    plan_path = plans_dir / "2025-10-05-relay.plan.json"
    _write_plan(plan_path, plan_id="2025-10-05-relay", impact_ref="relay-insight-outcome")
    missing_plan_path = plans_dir / "2025-10-06-missing.plan.json"
    _write_plan(missing_plan_path, plan_id="2025-10-06-missing", impact_ref=None)

    backlog_path = repo / "_plans" / "next-development.todo.json"
    backlog_payload = {
        "items": [
            {
                "id": "ND-001",
                "title": "Relay impact",
                "status": "in_progress",
                "plan_suggestion": "2025-10-05-relay",
                "priority": "high",
                "layer": "L2",
            }
        ]
    }
    backlog_path.write_text(json.dumps(backlog_payload, indent=2) + "\n", encoding="utf-8")

    summary_path = repo / "_report" / "impact" / "bridge" / "summary.json"
    markdown_path = repo / "_report" / "impact" / "bridge" / "dashboard.md"

    rc = bridge.main(
        [
            "--impact-log",
            str(impact_log),
            "--plans-dir",
            str(plans_dir),
            "--backlog",
            str(backlog_path),
            "--summary",
            str(summary_path),
            "--markdown",
            str(markdown_path),
        ]
    )
    assert rc == 0
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    entries = summary["entries"]
    assert len(entries) == 1
    linked = entries[0]["linked_plans"]
    assert linked and linked[0]["plan_id"] == "2025-10-05-relay"
    backlog_refs = entries[0]["linked_backlog"]
    assert backlog_refs and backlog_refs[0]["id"] == "ND-001"
    assert summary["stats"]["missing_impact_ref"] == 1
    assert markdown_path.read_text(encoding="utf-8").startswith("# Impact Bridge Dashboard")


def test_bridge_fail_on_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path
    monkeypatch.setattr(bridge, "ROOT", repo)
    impact_log = repo / "memory" / "impact" / "log.jsonl"
    impact_log.parent.mkdir(parents=True, exist_ok=True)
    impact_log.write_text("", encoding="utf-8")
    plans_dir = repo / "_plans"
    plans_dir.mkdir(parents=True)
    plan_path = plans_dir / "2025-10-07-no-impact.plan.json"
    _write_plan(plan_path, plan_id="2025-10-07-no-impact", impact_ref=None)
    backlog_path = repo / "_plans" / "next-development.todo.json"
    backlog_path.write_text(json.dumps({"items": []}) + "\n", encoding="utf-8")
    rc = bridge.main(
        [
            "--impact-log",
            str(impact_log),
            "--plans-dir",
            str(plans_dir),
            "--backlog",
            str(backlog_path),
            "--fail-on-missing",
        ]
    )
    assert rc == 1
