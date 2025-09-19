from __future__ import annotations

import json
from pathlib import Path

from tools.agent import bus_heartbeat


def _setup_paths(root: Path, monkeypatch) -> None:
    events_path = root / "_bus" / "events" / "events.jsonl"
    messages_dir = root / "_bus" / "messages"
    claims_dir = root / "_bus" / "claims"
    assignments_dir = root / "_bus" / "assignments"

    monkeypatch.setattr(bus_heartbeat, "ROOT", root)
    monkeypatch.setattr(bus_heartbeat, "EVENT_LOG", events_path)
    monkeypatch.setattr(bus_heartbeat, "MESSAGES_DIR", messages_dir)
    monkeypatch.setattr(bus_heartbeat, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(bus_heartbeat, "ASSIGNMENTS_DIR", assignments_dir)
    monkeypatch.setattr(bus_heartbeat, "PRIMARY_MANIFEST", root / "AGENT_MANIFEST.json")

    events_path.parent.mkdir(parents=True, exist_ok=True)
    messages_dir.mkdir(parents=True, exist_ok=True)
    claims_dir.mkdir(parents=True, exist_ok=True)
    assignments_dir.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _append_jsonl(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def test_bus_heartbeat_flags_stale_manager_and_idle_agent(tmp_path, monkeypatch):
    root = tmp_path
    _setup_paths(root, monkeypatch)

    # Manifest for agent + manager candidate
    _write_json(root / "AGENT_MANIFEST.json", {"agent_id": "codex-2"})
    _write_json(
        root / "AGENT_MANIFEST.codex-manager.json",
        {"agent_id": "codex-manager", "desired_roles": ["manager"]},
    )

    # Manager heartbeat older than threshold
    _append_jsonl(
        bus_heartbeat.EVENT_LOG,
        {
            "ts": "2025-09-18T22:00:00Z",
            "agent_id": "codex-manager",
            "event": "status",
            "summary": "heartbeat",
        },
    )

    # Active claim without recent activity -> should flag idle
    _write_json(
        bus_heartbeat.CLAIMS_DIR / "QUEUE-500.json",
        {
            "task_id": "QUEUE-500",
            "agent_id": "codex-3",
            "status": "active",
        },
    )

    exit_code = bus_heartbeat.main(
        [
            "--manager-window",
            "30",
            "--agent-window",
            "60",
            "--now",
            "2025-09-18T23:00:00Z",
            "--dry-run",
            "--no-bus-event",
            "--no-bus-message",
        ]
    )
    assert exit_code == 0

    receipt_dir = root / "_report" / "agent" / "codex-2" / "apoptosis-004" / "alerts"
    receipts = list(receipt_dir.glob("heartbeat-*.json"))
    assert len(receipts) == 1
    alert_data = json.loads(receipts[0].read_text(encoding="utf-8"))

    alert_types = {entry["type"] for entry in alert_data["alerts"]}
    assert alert_types == {"manager_heartbeat_stale", "agent_idle"}
    idle_entry = next(entry for entry in alert_data["alerts"] if entry["type"] == "agent_idle")
    assert idle_entry["tasks"] == ["QUEUE-500"]

    # Dry-run keeps bus event log untouched beyond the seed entry
    log_lines = bus_heartbeat.EVENT_LOG.read_text(encoding="utf-8").strip().splitlines()
    assert len(log_lines) == 1


def test_bus_heartbeat_emits_bus_event_and_message(tmp_path, monkeypatch):
    root = tmp_path
    _setup_paths(root, monkeypatch)

    from tools.agent import bus_message
    from tools.usage import logger as usage_logger

    # Redirect bus_message + usage logger paths into the sandbox root
    monkeypatch.setattr(bus_message, "ROOT", root)
    monkeypatch.setattr(bus_message, "MESSAGES_DIR", bus_heartbeat.MESSAGES_DIR)
    monkeypatch.setattr(bus_message, "MANIFEST_PATH", root / "AGENT_MANIFEST.json")
    monkeypatch.setattr(usage_logger, "ROOT", root)
    monkeypatch.setattr(usage_logger, "USAGE_DIR", root / "_report" / "usage")
    monkeypatch.setattr(usage_logger, "USAGE_LOG", usage_logger.USAGE_DIR / "tools.jsonl")

    _write_json(root / "AGENT_MANIFEST.json", {"agent_id": "codex-2"})
    _write_json(
        root / "AGENT_MANIFEST.codex-manager.json",
        {"agent_id": "codex-manager", "desired_roles": ["manager"]},
    )
    _append_jsonl(
        bus_heartbeat.EVENT_LOG,
        {
            "ts": "2025-09-18T00:00:00Z",
            "agent_id": "codex-manager",
            "event": "status",
            "summary": "heartbeat",
        },
    )
    _write_json(
        bus_heartbeat.CLAIMS_DIR / "QUEUE-600.json",
        {
            "task_id": "QUEUE-600",
            "agent_id": "codex-3",
            "status": "active",
        },
    )

    exit_code = bus_heartbeat.main(
        [
            "--manager-window",
            "30",
            "--agent-window",
            "120",
            "--now",
            "2025-09-18T03:00:00Z",
            "--task",
            "APOP-004",
            "--plan",
            "2025-09-20-bus-heartbeat-refresh",
            "--note",
            "test-run",
        ]
    )
    assert exit_code == 0

    log_lines = bus_heartbeat.EVENT_LOG.read_text(encoding="utf-8").strip().splitlines()
    assert len(log_lines) == 2
    alert_event = json.loads(log_lines[-1])
    assert alert_event["event"] == "alert"
    assert alert_event["severity"] == "high"
    assert alert_event["task_id"] == "APOP-004"
    assert alert_event["plan_id"] == "2025-09-20-bus-heartbeat-refresh"
    receipts = alert_event.get("receipts", [])
    assert receipts and receipts[0].startswith("_report/agent/codex-2/apoptosis-004/alerts/")

    message_path = bus_heartbeat.MESSAGES_DIR / f"{bus_heartbeat.DEFAULT_MESSAGE_TASK}.jsonl"
    assert message_path.exists()
    message_lines = message_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(message_lines) == 1
    bus_msg = json.loads(message_lines[0])
    assert bus_msg["type"] == bus_heartbeat.DEFAULT_MESSAGE_TYPE
    assert bus_msg["task_id"] == bus_heartbeat.DEFAULT_MESSAGE_TASK
    assert receipts[0] in bus_msg.get("receipts", [])

