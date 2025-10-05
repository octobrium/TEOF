import json
from pathlib import Path

import pytest

from tools.agent import bus_ping


def _configure_paths(tmp_path, monkeypatch):
    events_dir = tmp_path / "events"
    messages_dir = tmp_path / "messages"
    claims_dir = tmp_path / "claims"
    report_dir = tmp_path / "_report" / "agent"

    monkeypatch.setattr(bus_ping.bus_event, "EVENT_LOG", events_dir / "events.jsonl")
    monkeypatch.setattr(bus_ping.bus_event, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(bus_ping.bus_event, "AGENT_REPORT_DIR", report_dir)
    monkeypatch.setattr(bus_ping.bus_event, "MANIFEST_PATH", tmp_path / "manifest.json")

    monkeypatch.setattr(bus_ping.bus_message, "MESSAGES_DIR", messages_dir)
    monkeypatch.setattr(bus_ping.bus_message, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(bus_ping.bus_message, "AGENT_REPORT_DIR", report_dir)
    monkeypatch.setattr(bus_ping.bus_message, "MANIFEST_PATH", tmp_path / "manifest.json")

    monkeypatch.setattr(bus_ping, "MANIFEST_PATH", tmp_path / "manifest.json")

    events_dir.mkdir(parents=True, exist_ok=True)
    messages_dir.mkdir(parents=True, exist_ok=True)
    claims_dir.mkdir(parents=True, exist_ok=True)
    return events_dir, messages_dir, claims_dir, report_dir


def _write_manifest(tmp_path: Path, agent_id: str = "codex-4") -> None:
    (tmp_path / "manifest.json").write_text(json.dumps({"agent_id": agent_id}), encoding="utf-8")


def _write_claim(claims_dir: Path, task_id: str, agent_id: str) -> None:
    payload = {
        "task_id": task_id,
        "agent_id": agent_id,
        "status": "active",
        "branch": f"agent/{agent_id}/{task_id.lower()}",
        "claimed_at": "2025-09-20T00:00:00Z",
    }
    (claims_dir / f"{task_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_bus_ping_event_only(tmp_path, monkeypatch):
    events_dir, _, _, _ = _configure_paths(tmp_path, monkeypatch)
    _write_manifest(tmp_path)

    exit_code = bus_ping.main(["--summary", "checking in"])
    assert exit_code == 0

    log_path = events_dir / "events.jsonl"
    payload = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    assert payload["agent_id"] == "codex-4"
    assert payload["event"] == "status"
    assert payload["summary"].startswith("codex-4:")


def test_bus_ping_with_message(tmp_path, monkeypatch):
    events_dir, messages_dir, claims_dir, _ = _configure_paths(tmp_path, monkeypatch)
    _write_manifest(tmp_path, agent_id="codex-3")
    _write_claim(claims_dir, "QUEUE-010", "codex-3")

    exit_code = bus_ping.main(
        [
            "--task",
            "QUEUE-010",
            "--summary",
            "status update",
            "--message-task",
            "QUEUE-010",
            "--message-receipt",
            "_report/agent/codex-3/queue-010/notes.md",
        ]
    )
    assert exit_code == 0

    event_payload = json.loads((events_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert event_payload["task_id"] == "QUEUE-010"
    assert event_payload["summary"].startswith("codex-3:")

    message_payload = json.loads((messages_dir / "QUEUE-010.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert message_payload["from"] == "codex-3"
    assert message_payload["summary"].startswith("codex-3:")
    assert message_payload["receipts"] == ["_report/agent/codex-3/queue-010/notes.md"]


def test_bus_ping_requires_agent(tmp_path, monkeypatch):
    _configure_paths(tmp_path, monkeypatch)

    with pytest.raises(SystemExit) as exc:
        bus_ping.main(["--summary", "missing manifest"])  # no manifest, no --agent
    assert "agent id required" in str(exc.value)
