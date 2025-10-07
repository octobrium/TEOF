import json
from datetime import datetime, timedelta, timezone

import pytest

from tools.agent import bus_status


def _setup_bus(tmp_path, monkeypatch):
    claims_dir = tmp_path / "claims"
    claims_dir.mkdir(parents=True)
    events_dir = tmp_path / "events"
    events_dir.parent.mkdir(parents=True, exist_ok=True)
    events_log = events_dir / "events.jsonl"
    assignments_dir = tmp_path / "assignments"
    assignments_dir.mkdir()

    now = datetime(2025, 9, 18, 0, 30, tzinfo=timezone.utc)
    def iso(offset_minutes: int) -> str:
        return (now + timedelta(minutes=offset_minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")

    def write_claim(path, task, agent, status, claimed, released=None):
        payload = {
            "task_id": task,
            "agent_id": agent,
            "branch": f"agent/{agent}/{task.lower()}",
            "status": status,
            "plan_id": "2025-09-18-agent-bus-status",
            "claimed_at": claimed,
        }
        if released:
            payload["released_at"] = released
        path.write_text(json.dumps(payload), encoding="utf-8")

    write_claim(
        claims_dir / "QUEUE-010.json",
        "QUEUE-010",
        "codex-1",
        "active",
        iso(0),
    )
    write_claim(
        claims_dir / "QUEUE-011.json",
        "QUEUE-011",
        "codex-2",
        "done",
        iso(1),
        released=iso(5),
    )

    events = [
        {
            "ts": iso(0),
            "agent_id": "codex-1",
            "event": "status",
            "task_id": "QUEUE-010",
            "summary": "manager heartbeat",
            "shift": "mid",
            "severity": "medium",
        },
        {"ts": iso(2), "agent_id": "codex-2", "event": "complete", "task_id": "QUEUE-011", "summary": "complete"},
        {
            "ts": iso(3),
            "agent_id": "codex-3",
            "event": "alert",
            "task_id": "QUEUE-012",
            "summary": "high severity alert",
            "severity": "high",
        },
    ]
    events_dir.mkdir(parents=True, exist_ok=True)
    with events_log.open("w", encoding="utf-8") as fh:
        for entry in events:
            fh.write(json.dumps(entry) + "\n")

    assignment_payload = {
        "task_id": "QUEUE-010",
        "manager": "codex-1",
        "status": "unassigned",
    }
    (assignments_dir / "QUEUE-010.json").write_text(json.dumps(assignment_payload), encoding="utf-8")

    manifest = tmp_path / "AGENT_MANIFEST.codex-1.json"
    manifest.write_text(
        json.dumps({"agent_id": "codex-1", "desired_roles": ["manager"]}),
        encoding="utf-8",
    )

    class _FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return now.replace(tzinfo=None)
            return now.astimezone(tz)

    monkeypatch.setattr(bus_status, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(bus_status, "EVENT_LOG", events_log)
    monkeypatch.setattr(bus_status, "ASSIGNMENTS_DIR", assignments_dir)
    monkeypatch.setattr(bus_status, "ROOT", tmp_path)
    monkeypatch.setattr(bus_status, "datetime", _FixedDatetime)
    return iso


def test_bus_status_filters_by_agent(tmp_path, monkeypatch, capsys):
    _setup_bus(tmp_path, monkeypatch)
    exit_code = bus_status.main(["--limit", "5", "--agent", "codex-1"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Managers (window 30m):" in out
    assert "codex-1" in out
    assert "codex-2" not in out
    assert ":: codex-1 ::" in out
    assert "sev=medium" in out


def test_bus_status_active_only(tmp_path, monkeypatch, capsys):
    _setup_bus(tmp_path, monkeypatch)
    exit_code = bus_status.main(["--active-only", "--limit", "5"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Managers (window 30m):" in out
    claims_section = out.split("Active claims:", 1)[1]
    claims_section = claims_section.split("Recent events:", 1)[0]
    assert "QUEUE-010" in claims_section
    assert "QUEUE-011" not in claims_section


def test_bus_status_json_output(tmp_path, monkeypatch, capsys):
    _setup_bus(tmp_path, monkeypatch)
    exit_code = bus_status.main(["--json", "--agent", "codex-1", "--limit", "5"])
    assert exit_code == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["filters"]["agents"] == ["codex-1"]
    assert payload["filters"]["active_only"] is False
    assert payload["filters"]["preset"] is None
    assert payload["filters"]["severity"] == []
    assert payload["filters"]["window_hours"] == bus_status.DEFAULT_WINDOW_HOURS
    assert payload["filters"]["manager_window"] == bus_status.DEFAULT_MANAGER_WINDOW_MINUTES
    assert len(payload["claims"]) == 1
    assert payload["claims"][0]["agent_id"] == "codex-1"
    assert len(payload["events"]) == 1
    assert payload["events"][0]["agent_id"] == "codex-1"
    assert payload["events"][0]["severity"] == "medium"
    assert payload["filters"]["since"] is None
    manager_status = payload["manager_status"]
    assert manager_status["active"][0]["agent_id"] == "codex-1"
    assert manager_status["active"][0]["summary"] == "manager heartbeat"
    assert manager_status["active"][0]["meta"].get("shift") == "mid"
    assert not manager_status["stale"]
    assert not manager_status["missing"]


def test_bus_status_since_filters_events(tmp_path, monkeypatch, capsys):
    iso = _setup_bus(tmp_path, monkeypatch)
    cutoff = iso(1)
    exit_code = bus_status.main(["--json", "--since", cutoff, "--limit", "5", "--agent", "codex-2"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["filters"]["since"] == cutoff
    assert len(payload["claims"]) == 1
    assert len(payload["events"]) == 1
    assert payload["events"][0]["agent_id"] == "codex-2"
    assert payload["filters"]["severity"] == []


def test_bus_status_severity_filter(tmp_path, monkeypatch, capsys):
    _setup_bus(tmp_path, monkeypatch)
    exit_code = bus_status.main(["--json", "--severity", "high", "--agent", "codex-3", "--limit", "5"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["filters"]["severity"] == ["high"]
    assert payload["filters"]["agents"] == ["codex-3"]
    assert len(payload["events"]) == 1
    assert payload["events"][0]["severity"] == "high"


def test_bus_status_defaults_to_manifest_agent(tmp_path, monkeypatch, capsys):
    _setup_bus(tmp_path, monkeypatch)
    manifest = tmp_path / "AGENT_MANIFEST.json"
    manifest.write_text(json.dumps({"agent_id": "codex-1"}), encoding="utf-8")

    exit_code = bus_status.main(["--json", "--limit", "5"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["filters"]["agents"] == ["codex-1"]
    assert len(payload["claims"]) == 1
    assert all(claim["agent_id"] == "codex-1" for claim in payload["claims"])


def test_manager_warning_when_no_recent_heartbeat(tmp_path, monkeypatch, capsys):
    _setup_bus(tmp_path, monkeypatch)

    future = datetime(2025, 9, 18, 1, 10, tzinfo=timezone.utc)

    class _LateDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return future.replace(tzinfo=None)
            return future.astimezone(tz)

    monkeypatch.setattr(bus_status, "datetime", _LateDatetime)
    exit_code = bus_status.main(["--limit", "5", "--manager-window", "10"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "WARNING: No manager heartbeat within window." in out
    assert "Stale:" in out


def test_bus_status_window_hours_zero_disables_filter(tmp_path, monkeypatch, capsys):
    _setup_bus(tmp_path, monkeypatch)
    events_log = tmp_path / "events" / "events.jsonl"
    older = datetime(2025, 9, 16, 0, 30, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with events_log.open("a", encoding="utf-8") as fh:
        fh.write(
            json.dumps(
                {
                    "ts": older,
                    "agent_id": "codex-1",
                    "event": "status",
                    "task_id": "QUEUE-999",
                    "summary": "legacy heartbeat",
                }
            )
            + "\n"
        )

    # Default window hides the legacy event
    exit_code = bus_status.main(["--json", "--limit", "10"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert all(event.get("task_id") != "QUEUE-999" for event in payload["events"])

    # Disabling the window surfaces all events
    exit_code = bus_status.main(["--json", "--limit", "10", "--window-hours", "0"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    tasks = {event.get("task_id") for event in payload["events"]}
    assert "QUEUE-999" in tasks
    assert payload["filters"]["window_hours"] == 0


def test_bus_status_presets_apply_defaults(tmp_path, monkeypatch, capsys):
    _setup_bus(tmp_path, monkeypatch)
    exit_code = bus_status.main(["--json", "--preset", "support"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    filters = payload["filters"]
    assert filters["preset"] == "support"
    assert filters["limit"] == 20
    assert filters["window_hours"] == pytest.approx(6.0)
    assert filters["active_only"] is True


def test_bus_status_summary_output(tmp_path, monkeypatch, capsys):
    _setup_bus(tmp_path, monkeypatch)
    exit_code = bus_status.main(["--summary", "--preset", "manager"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Summary" in out
    assert "manager heartbeat" in out
