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
    assert data["plans"][0]["plan_id"] == "PLAN-001"
    # PLAN-002 should flag missing receipts
    missing_plan = next(item for item in data["plans"] if item["plan_id"] == "PLAN-002")
    assert missing_plan["missing_receipts"] is True
    assert any("PLAN-002" in alert for alert in data["alerts"])
    managers = data["heartbeats"]["managers"]
    assert managers[0]["agent_id"] == "codex-1"
    assert managers[0]["state"] == "active"
    agents = {record["agent_id"]: record for record in data["heartbeats"]["agents"]}
    assert agents["codex-2"]["state"] == "stale"
    directives = data["manager_directives"]
    assert directives[-1]["summary"] == "idle agent available"
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
