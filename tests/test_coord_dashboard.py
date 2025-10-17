import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from tools.agent import coord_dashboard


ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


@pytest.fixture(autouse=True)
def patch_usage(monkeypatch):
    monkeypatch.setattr(coord_dashboard, "record_usage", lambda *args, **kwargs: None)


def iso(ts: datetime) -> str:
    return ts.strftime(ISO_FMT)


@pytest.fixture
def dashboard_env(tmp_path, monkeypatch):
    now = datetime(2025, 9, 21, 0, 30, tzinfo=timezone.utc)
    monkeypatch.setattr(coord_dashboard, "utcnow", lambda: now)

    plans_dir = tmp_path / coord_dashboard.PLANS_DIRNAME
    plans_dir.mkdir(parents=True)
    receipts_dir = tmp_path / "_report" / "agent" / "codex-4" / "apoptosis-009"
    receipts_dir.mkdir(parents=True)
    receipt_path = receipts_dir / "design.md"
    receipt_path.write_text("design receipt", encoding="utf-8")

    plan_ok = {
        "plan_id": "PLAN-001",
        "actor": "codex-4",
        "status": "in_progress",
        "steps": [
            {
                "id": "S1",
                "status": "completed",
                "receipts": [receipt_path.relative_to(tmp_path).as_posix()],
            },
            {"id": "S2", "status": "queued"},
        ],
        "checkpoint": {"status": "pending"},
    }
    (plans_dir / "plan-001.plan.json").write_text(json.dumps(plan_ok), encoding="utf-8")

    plan_missing = {
        "plan_id": "PLAN-002",
        "actor": "codex-3",
        "status": "queued",
        "steps": [
            {
                "id": "S1",
                "status": "completed",
                "receipts": [],
            }
        ],
    }
    (plans_dir / "plan-002.plan.json").write_text(json.dumps(plan_missing), encoding="utf-8")

    plan_done = {
        "plan_id": "PLAN-003",
        "actor": "codex-2",
        "status": "done",
        "steps": [],
    }
    (plans_dir / "plan-003.plan.json").write_text(json.dumps(plan_done), encoding="utf-8")

    heartbeat_plan = {
        "plan_id": "2025-09-19-heartbeat-docs-codex3",
        "actor": "codex-3",
        "status": "queued",
        "steps": [
            {"id": "S1", "status": "queued"},
            {"id": "S2", "status": "queued"},
        ],
    }
    (plans_dir / "heartbeat-docs.plan.json").write_text(json.dumps(heartbeat_plan), encoding="utf-8")

    claims_dir = tmp_path / coord_dashboard.CLAIMS_DIRNAME
    claims_dir.mkdir(parents=True)
    claim_payload = {
        "agent_id": "codex-4",
        "status": "active",
        "branch": "agent/codex-4/apoptosis-009",
        "plan_id": "PLAN-001",
        "claimed_at": iso(now - timedelta(minutes=5)),
    }
    (claims_dir / "APOP-009.json").write_text(json.dumps(claim_payload), encoding="utf-8")

    claim_done = {
        "agent_id": "codex-3",
        "status": "done",
        "plan_id": "PLAN-003",
        "claimed_at": iso(now - timedelta(days=1)),
        "released_at": iso(now - timedelta(hours=12)),
    }
    (claims_dir / "APOP-010.json").write_text(json.dumps(claim_done), encoding="utf-8")

    events_path = tmp_path / coord_dashboard.EVENT_LOG
    events_path.parent.mkdir(parents=True, exist_ok=True)
    events = [
        {
            "ts": iso(now - timedelta(minutes=10)),
            "agent_id": "codex-1",
            "event": "status",
            "summary": "manager ping",
        },
        {
            "ts": iso(now - timedelta(minutes=15)),
            "agent_id": "codex-5",
            "event": "alert",
            "summary": "high severity escalation",
            "severity": "high",
            "task_id": "QUEUE-999",
        },
        {
            "ts": iso(now - timedelta(minutes=90)),
            "agent_id": "codex-2",
            "event": "status",
            "summary": "stale agent",
        },
        {
            "ts": iso(now - timedelta(minutes=5)),
            "agent_id": "codex-4",
            "event": "handshake",
            "summary": "active agent",
        },
        {
            "ts": iso(now - timedelta(days=2)),
            "agent_id": "codex-observer",
            "event": "status",
            "summary": "retired persona",
        },
        {
            "ts": iso(now - timedelta(hours=30)),
            "agent_id": "codex-6",
            "event": "alert",
            "summary": "expired high severity",
            "severity": "high",
        },
    ]
    events_path.write_text("\n".join(json.dumps(item) for item in events), encoding="utf-8")

    manager_manifest = {
        "agent_id": "codex-1",
        "desired_roles": ["manager"],
    }
    (tmp_path / "AGENT_MANIFEST.codex-1.json").write_text(json.dumps(manager_manifest), encoding="utf-8")

    messages_path = tmp_path / coord_dashboard.MANAGER_MESSAGES
    messages_path.parent.mkdir(parents=True, exist_ok=True)
    directives = [
        {
            "ts": iso(now - timedelta(minutes=20)),
            "from": "codex-1",
            "type": "status",
            "summary": "check dashboard progress",
        },
        {
            "ts": iso(now - timedelta(minutes=2)),
            "from": "codex-2",
            "type": "note",
            "summary": "idle agent available",
        },
    ]
    messages_path.write_text("\n".join(json.dumps(item) for item in directives), encoding="utf-8")

    dirty_dir = tmp_path / coord_dashboard.SESSION_DIRNAME / "codex-2" / coord_dashboard.DIRTY_HANDOFF_SUBDIR
    dirty_dir.mkdir(parents=True, exist_ok=True)
    (dirty_dir / "dirty-20250920T234500Z.txt").write_text(
        "# dirty handoff\n# agent=codex-2\n# captured_at=2025-09-20T23:45:00Z\n\n M docs/a.txt\n",
        encoding="utf-8",
    )
    (dirty_dir / "dirty-20250921T002500Z.txt").write_text(
        "# dirty handoff\n# agent=codex-2\n# captured_at=2025-09-21T00:25:00Z\n\n M docs/b.txt\n?? new.md\n",
        encoding="utf-8",
    )

    summary_dir = tmp_path / "_report" / "planner" / "validate"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_payload = {
        "generated_at": iso(now),
        "strict": True,
        "exit_code": 0,
        "plans": [
            {
                "path": "_plans/plan-001.plan.json",
                "ok": True,
                "errors": [],
                "plan_id": "PLAN-001",
                "queue_warnings": [],
            },
            {
                "path": "_plans/plan-002.plan.json",
                "ok": True,
                "errors": [],
                "plan_id": "PLAN-002",
                "queue_warnings": [
                    {
                        "plan_id": "PLAN-002",
                        "queue_ref": "queue/999-sync.md",
                        "issue": "systemic_targets_mismatch",
                        "message": "PLAN-002 systemic targets mismatch with queue/999-sync.md",
                    }
                ],
            },
        ],
    }
    (summary_dir / "summary-latest.json").write_text(
        json.dumps(summary_payload, indent=2),
        encoding="utf-8",
    )

    return tmp_path, now


def test_json_report(tmp_path, dashboard_env, capsys):
    root, now = dashboard_env
    output = tmp_path / "out.json"
    rc = coord_dashboard.main(
        [
            "report",
            "--format",
            "json",
            "--output",
            str(output),
            "--root",
            str(root),
            "--messages",
            "5",
        ]
    )
    assert rc == 0
    data = json.loads(output.read_text(encoding="utf-8"))
    plan_ids = {plan["plan_id"] for plan in data["plans"]}
    assert "PLAN-001" in plan_ids
    # PLAN-002 should flag missing receipts
    missing_plan = next(item for item in data["plans"] if item["plan_id"] == "PLAN-002")
    assert missing_plan["missing_receipts"] is True
    assert any("PLAN PLAN-002" in alert or "Plan PLAN-002" in alert for alert in data["alerts"])
    unclaimed = {entry["plan_id"] for entry in data["unclaimed_plans"]}
    assert "PLAN-002" in unclaimed
    managers = data["heartbeats"]["managers"]
    assert managers[0]["agent_id"] == "codex-1"
    assert managers[0]["state"] == "active"
    agents = {record["agent_id"]: record for record in data["heartbeats"]["agents"]}
    assert agents["codex-2"]["state"] == "stale"
    assert "codex-observer" not in agents
    directives = data["manager_directives"]
    assert directives[-1]["summary"] == "idle agent available"
    pruning = data["pruning_candidates"]
    plan_inventory = {entry["plan_id"] for entry in pruning.get("plans", [])}
    assert "PLAN-003" in plan_inventory
    claim_inventory = {entry["task_id"] for entry in pruning.get("claims", [])}
    assert "APOP-010" in claim_inventory
    heartbeat_meta = data["heartbeat_meta"]
    assert heartbeat_meta["manager_window_minutes"] == coord_dashboard.DEFAULT_MANAGER_WINDOW_MINUTES
    assert heartbeat_meta["agent_window_minutes"] == coord_dashboard.DEFAULT_AGENT_WINDOW_MINUTES
    automation_plans = {item["plan_id"] for item in heartbeat_meta["automation_plans"]}
    assert "2025-09-19-heartbeat-docs-codex3" in automation_plans
    digest = data["severity_digest"]
    assert len(digest) == 1
    assert digest[0]["agent_id"] == "codex-5"
    assert digest[0]["task_id"] == "QUEUE-999"
    digest_meta = data["severity_digest_meta"]
    assert digest_meta["severities"] == list(coord_dashboard.SEVERITY_DIGEST_LEVELS)
    dirty = data["dirty_handoffs"]
    assert dirty, "expected dirty handoff summary"
    dirty_entry = next(entry for entry in dirty if entry["agent_id"] == "codex-2")
    assert dirty_entry["pending_count"] == 2
    assert "docs/b.txt" in ";".join(dirty_entry.get("status_preview", []))
    assert any("Dirty handoff pending for codex-2" in alert for alert in data["alerts"])
    warnings = data["planner_queue_warnings"]
    assert warnings and warnings[0]["issue"] == "systemic_targets_mismatch"
    assert any("Queue warning" in alert for alert in data["alerts"])
    captured = capsys.readouterr().out
    assert "Output written" in captured


def test_markdown_default_output(tmp_path, dashboard_env):
    root, now = dashboard_env
    rc = coord_dashboard.main([
        "report",
        "--format",
        "markdown",
        "--root",
        str(root),
    ])
    assert rc == 0
    expected = root / "_report" / "manager" / f"coordination-dashboard-{iso(now)}.md"
    assert expected.exists()
    content = expected.read_text(encoding="utf-8")
    assert "# Coordination Dashboard" in content
    assert "PLAN-001" in content
    assert "- Heartbeat codex-2 is stale" in content
    assert "idle agent available" in content
    assert "## Unclaimed Plans" in content
    assert "PLAN-002" in content
    assert "Heartbeat windows — managers: 30m, agents: 60m." in content
    assert "Heartbeat automation in flight" in content
    assert "2025-09-19-heartbeat-docs-codex3" in content
    assert "## Dirty Handoffs" in content
    assert "codex-2" in content
    assert "## Severity Digest" in content
    assert "QUEUE-999" in content
    assert "## Planner Queue Warnings" in content
    assert "PLAN-002" in content
