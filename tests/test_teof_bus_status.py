import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import teof.bootloader as bootloader
from tools.agent import bus_status


def _setup_bus(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    claims_dir = tmp_path / "claims"
    claims_dir.mkdir(parents=True)
    events_log = tmp_path / "events.jsonl"
    events_log.parent.mkdir(parents=True, exist_ok=True)
    assignments_dir = tmp_path / "assignments"
    assignments_dir.mkdir()

    now = datetime(2025, 9, 18, 0, 30, tzinfo=timezone.utc)

    def iso(offset_minutes: int) -> str:
        return (now + timedelta(minutes=offset_minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")

    claim_payload = {
        "task_id": "QUEUE-010",
        "agent_id": "codex-1",
        "branch": "agent/codex-1/queue-010",
        "status": "active",
        "plan_id": "2025-09-18-agent-bus-status",
        "claimed_at": iso(0),
    }
    (claims_dir / "QUEUE-010.json").write_text(json.dumps(claim_payload), encoding="utf-8")

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
    ]
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


def test_teof_bus_status_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup_bus(tmp_path, monkeypatch)

    exit_code = bootloader.main([
        "bus_status",
        "--json",
        "--agent",
        "codex-1",
        "--limit",
        "5",
        "--events-path",
        str(bus_status.EVENT_LOG),
    ])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["filters"]["agents"] == ["codex-1"]
    assert payload["claims"][0]["task_id"] == "QUEUE-010"
    assert payload["events"][0]["agent_id"] == "codex-1"


def test_teof_bus_status_summary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup_bus(tmp_path, monkeypatch)

    exit_code = bootloader.main([
        "bus_status",
        "--summary",
        "--limit",
        "5",
        "--events-path",
        str(bus_status.EVENT_LOG),
    ])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Summary" in out
    assert "QUEUE-010" in out
