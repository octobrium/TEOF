import json
from pathlib import Path

import pytest

from tools.agent import bus_event


def setup_bus_event(monkeypatch, tmp_path):
    log_path = tmp_path / "events.jsonl"
    manifest_path = tmp_path / "AGENT_MANIFEST.json"
    claims_dir = tmp_path / "claims"
    monkeypatch.setattr(bus_event, "ROOT", tmp_path)
    monkeypatch.setattr(bus_event, "EVENT_LOG", log_path)
    monkeypatch.setattr(bus_event, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(bus_event, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(bus_event, "AGENT_REPORT_DIR", tmp_path / "_report" / "agent")
    claims_dir.mkdir(parents=True, exist_ok=True)
    return log_path, manifest_path, claims_dir


def read_events(path: Path) -> list[dict]:
    data = path.read_text(encoding="utf-8")
    return [json.loads(line) for line in data.splitlines() if line.strip()]


def test_bus_event_requires_agent(monkeypatch, tmp_path):
    log_path, manifest_path, _ = setup_bus_event(monkeypatch, tmp_path)
    assert not log_path.exists()
    assert not manifest_path.exists()

    with pytest.raises(SystemExit):
        bus_event.main(
            [
                "log",
                "--event",
                "status",
                "--summary",
                "no agent provided",
            ]
        )

    assert not log_path.exists()


def test_bus_event_uses_manifest_default(monkeypatch, tmp_path):
    log_path, manifest_path, claims_dir = setup_bus_event(monkeypatch, tmp_path)
    manifest_path.write_text(json.dumps({"agent_id": "codex-3"}), encoding="utf-8")
    claim_path = claims_dir / "QUEUE-000.json"
    claim_path.write_text(
        json.dumps(
            {
                "task_id": "QUEUE-000",
                "agent_id": "codex-3",
                "status": "active",
                "branch": "agent/codex-3/queue-000",
                "claimed_at": "2025-09-18T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    rc = bus_event.main(
        [
            "log",
            "--event",
            "handshake",
            "--summary",
            "using manifest default",
        ]
    )
    assert rc == 0

    events = read_events(log_path)
    assert len(events) == 1
    payload = events[0]
    assert payload["agent_id"] == "codex-3"
    assert payload["event"] == "handshake"
    assert payload["summary"] == "using manifest default"


def test_bus_event_records_optional_fields(monkeypatch, tmp_path):
    log_path, _, claims_dir = setup_bus_event(monkeypatch, tmp_path)
    claim_path = claims_dir / "QUEUE-003.json"
    claim_path.write_text(
        json.dumps(
            {
                "task_id": "QUEUE-003",
                "agent_id": "codex-3",
                "status": "active",
                "branch": "agent/codex-3/queue-003",
                "claimed_at": "2025-09-18T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    rc = bus_event.main(
        [
            "log",
            "--agent",
            "codex-3",
            "--event",
            "status",
            "--summary",
            "added extras",
            "--task",
            "QUEUE-003",
            "--branch",
            "agent/codex-3/queue-003",
            "--plan",
            "2025-09-18-agent-bus-cli-tests",
            "--receipt",
            "_report/example.json",
            "--extra",
            "reviewer=codex-1",
            "--severity",
            "medium",
        ]
    )
    assert rc == 0

    events = read_events(log_path)
    assert len(events) == 1
    payload = events[0]
    assert payload["agent_id"] == "codex-3"
    assert payload["event"] == "status"
    assert payload["summary"] == "added extras"
    assert payload.get("task_id") == "QUEUE-003"
    assert payload.get("branch") == "agent/codex-3/queue-003"
    assert payload.get("plan_id") == "2025-09-18-agent-bus-cli-tests"
    assert payload.get("receipts") == ["_report/example.json"]
    assert payload.get("reviewer") == "codex-1"
    assert payload.get("severity") == "medium"


def test_bus_event_rejects_invalid_severity(monkeypatch, tmp_path):
    log_path, manifest_path, claims_dir = setup_bus_event(monkeypatch, tmp_path)
    manifest_path.write_text(json.dumps({"agent_id": "codex-3"}), encoding="utf-8")
    claims_dir.joinpath("QUEUE-001.json").write_text(
        json.dumps(
            {
                "task_id": "QUEUE-001",
                "agent_id": "codex-3",
                "status": "active",
                "branch": "agent/codex-3/queue-001",
                "claimed_at": "2025-09-18T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit):
        bus_event.main(
            [
                "log",
                "--event",
                "status",
                "--summary",
                "bad severity",
                "--task",
                "QUEUE-001",
                "--severity",
                "critical",
            ]
        )

    assert not log_path.exists()


def test_bus_event_rejects_foreign_claim(monkeypatch, tmp_path):
    log_path, _, claims_dir = setup_bus_event(monkeypatch, tmp_path)
    error_log = tmp_path / "_report" / "agent" / "codex-4" / "errors.jsonl"
    claims_dir.joinpath("QUEUE-123.json").write_text(
        json.dumps(
            {
                "task_id": "QUEUE-123",
                "agent_id": "codex-3",
                "status": "active",
                "branch": "agent/codex-3/queue-123",
                "claimed_at": "2025-09-18T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as exc:
        bus_event.main(
            [
                "log",
                "--agent",
                "codex-4",
                "--event",
                "status",
                "--summary",
                "should fail",
                "--task",
                "QUEUE-123",
            ]
        )
    message = str(exc.value)
    assert "claimed by codex-3" in message
    assert "before logging status" in message
    assert not log_path.exists()
    assert error_log.exists()
    entries = [json.loads(line) for line in error_log.read_text(encoding="utf-8").splitlines() if line]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["agent_id"] == "codex-4"
    assert entry["event"] == "status"
    assert entry["task_id"] == "QUEUE-123"
    assert entry["claim_owner"] == "codex-3"
    assert entry["claim_status"] == "active"


def test_bus_event_logs_missing_claim(monkeypatch, tmp_path):
    log_path, _, _ = setup_bus_event(monkeypatch, tmp_path)
    errors_path = tmp_path / "_report" / "agent" / "codex-5" / "errors.jsonl"

    with pytest.raises(SystemExit) as exc:
        bus_event.main(
            [
                "log",
                "--agent",
                "codex-5",
                "--event",
                "status",
                "--summary",
                "missing claim",
                "--task",
                "QUEUE-404",
            ]
        )

    assert "QUEUE-404" in str(exc.value)
    assert not log_path.exists()
    assert errors_path.exists()
    items = [json.loads(line) for line in errors_path.read_text(encoding="utf-8").splitlines() if line]
    assert len(items) == 1
    record = items[0]
    assert record["agent_id"] == "codex-5"
    assert record["event"] == "status"
    assert record["task_id"] == "QUEUE-404"
    assert record.get("claim_owner") is None
    assert record.get("claim_status") is None


def test_bus_event_allows_terminal_claim(monkeypatch, tmp_path):
    log_path, _, claims_dir = setup_bus_event(monkeypatch, tmp_path)
    claims_dir.joinpath("QUEUE-777.json").write_text(
        json.dumps(
            {
                "task_id": "QUEUE-777",
                "agent_id": "codex-3",
                "status": "done",
                "branch": "agent/codex-3/queue-777",
                "claimed_at": "2025-09-18T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    rc = bus_event.main(
        [
            "log",
            "--agent",
            "codex-manager",
            "--event",
            "status",
            "--summary",
            "post-completion note",
            "--task",
            "QUEUE-777",
        ]
    )
    assert rc == 0
    events = read_events(log_path)
    assert len(events) == 1
