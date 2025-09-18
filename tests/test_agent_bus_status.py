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
        {"ts": iso(0), "agent_id": "codex-1", "event": "claim", "task_id": "QUEUE-010", "summary": "claimed"},
        {"ts": iso(2), "agent_id": "codex-2", "event": "complete", "task_id": "QUEUE-011", "summary": "complete"},
    ]
    events_dir.mkdir(parents=True, exist_ok=True)
    with events_log.open("w", encoding="utf-8") as fh:
        for entry in events:
            fh.write(json.dumps(entry) + "\n")

    monkeypatch.setattr(bus_status, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(bus_status, "EVENT_LOG", events_log)
    monkeypatch.setattr(bus_status, "ROOT", tmp_path)


def test_bus_status_filters_by_agent(tmp_path, monkeypatch, capsys):
    _setup_bus(tmp_path, monkeypatch)
    exit_code = bus_status.main(["--limit", "5", "--agent", "codex-1"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "codex-1" in out
    assert "codex-2" not in out
    assert ":: codex-1 ::" in out


def test_bus_status_active_only(tmp_path, monkeypatch, capsys):
    _setup_bus(tmp_path, monkeypatch)
    exit_code = bus_status.main(["--active-only", "--limit", "5"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "QUEUE-010" in out
    claims_section = out.split("\n\nRecent events:")[0]
    assert "QUEUE-011" not in claims_section


def test_bus_status_json_output(tmp_path, monkeypatch, capsys):
    _setup_bus(tmp_path, monkeypatch)
    exit_code = bus_status.main(["--json", "--agent", "codex-1", "--limit", "5"])
    assert exit_code == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["filters"]["agents"] == ["codex-1"]
    assert payload["filters"]["active_only"] is False
    assert len(payload["claims"]) == 1
    assert payload["claims"][0]["agent_id"] == "codex-1"
    assert len(payload["events"]) == 1
    assert payload["events"][0]["agent_id"] == "codex-1"
