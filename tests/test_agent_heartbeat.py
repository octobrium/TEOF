import json
from pathlib import Path

from tools.agent import heartbeat, bus_event


def test_emit_status_writes_event(tmp_path, monkeypatch):
    event_log = tmp_path / "events.jsonl"
    report_dir = tmp_path / "_report" / "agent"
    monkeypatch.setattr(bus_event, "EVENT_LOG", event_log)
    monkeypatch.setattr(bus_event, "AGENT_REPORT_DIR", report_dir)
    monkeypatch.setattr(bus_event, "CLAIMS_DIR", tmp_path / "claims")
    monkeypatch.setattr(bus_event, "ROOT", tmp_path)
    manifest_path = tmp_path / "AGENT_MANIFEST.json"
    manifest_path.write_text(json.dumps({"agent_id": "codex-2"}), encoding="utf-8")
    monkeypatch.setattr(bus_event, "MANIFEST_PATH", manifest_path)

    payload = heartbeat.emit_status(
        "codex-2",
        "Session wrap",
        extras={"shift": "mid"},
    )

    assert payload["agent_id"] == "codex-2"
    assert payload["summary"] == "Session wrap"
    assert payload["extras"]["shift"] == "mid"

    contents = event_log.read_text(encoding="utf-8").strip().splitlines()
    assert contents
    event = json.loads(contents[-1])
    assert event["agent_id"] == "codex-2"
    assert event["event"] == "status"
    assert event["summary"] == "Session wrap"
    assert event["shift"] == "mid"


def test_emit_status_dry_run_prints_payload(tmp_path, capsys, monkeypatch):
    # Ensure no event file is touched when dry_run=True
    event_log = tmp_path / "events.jsonl"
    monkeypatch.setattr(bus_event, "EVENT_LOG", event_log)
    manifest_path = tmp_path / "AGENT_MANIFEST.json"
    manifest_path.write_text(json.dumps({"agent_id": "codex-2"}), encoding="utf-8")
    monkeypatch.setattr(bus_event, "MANIFEST_PATH", manifest_path)

    payload = heartbeat.emit_status(
        "codex-2",
        "Dry run",
        extras={"shift": "late"},
        dry_run=True,
    )

    out = capsys.readouterr().out
    assert "Dry run" in out
    assert "shift" in out
    assert not event_log.exists()
    assert payload["extras"]["shift"] == "late"
