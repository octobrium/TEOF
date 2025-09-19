import json
from pathlib import Path

import pytest

from tools.agent import task_assign, bus_message
from tools.receipts import scaffold as receipt_scaffold


def setup_env(tmp_path, monkeypatch):
    assign_dir = tmp_path / "assignments"
    messages_dir = tmp_path / "messages"
    claims_dir = tmp_path / "claims"
    tasks_file = tmp_path / "tasks" / "tasks.json"
    manifest = tmp_path / "AGENT_MANIFEST.json"
    manifest.write_text(json.dumps({"agent_id": "codex-manager"}), encoding="utf-8")
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    tasks_file.write_text(json.dumps({"tasks": []}), encoding="utf-8")

    monkeypatch.setattr(task_assign, "ASSIGN_DIR", assign_dir)
    monkeypatch.setattr(task_assign, "MESSAGES_DIR", messages_dir)
    monkeypatch.setattr(task_assign, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(task_assign, "TASKS_FILE", tasks_file)
    monkeypatch.setattr(task_assign, "MANIFEST", manifest)
    monkeypatch.setattr(task_assign, "record_usage", lambda *args, **kwargs: None)
    monkeypatch.setattr(task_assign, "ROOT", tmp_path)

    monkeypatch.setattr(bus_message, "MESSAGES_DIR", messages_dir)
    monkeypatch.setattr(bus_message, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(bus_message, "record_usage", lambda *args, **kwargs: None)

    monkeypatch.setattr(task_assign.bus_claim, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(task_assign.bus_claim, "ASSIGNMENTS_DIR", assign_dir)
    monkeypatch.setattr(task_assign.bus_claim, "ROOT", tmp_path)

    monkeypatch.setattr(receipt_scaffold, "ROOT", tmp_path)
    monkeypatch.setattr(receipt_scaffold, "REPORT_ROOT", tmp_path / "_report" / "agent")
    monkeypatch.setattr(task_assign, "scaffold_claim", receipt_scaffold.scaffold_claim)
    monkeypatch.setattr(task_assign, "format_created", receipt_scaffold.format_created)

    return assign_dir, messages_dir, claims_dir, tasks_file


def test_task_assign_records_assignment(tmp_path, monkeypatch, capsys):
    assign_dir, messages_dir, claims_dir, tasks_file = setup_env(tmp_path, monkeypatch)

    rc = task_assign.main(
        [
            "--task",
            "QUEUE-006",
            "--engineer",
            "codex-2",
            "--plan",
            "2025-09-18-task-assign-bus-message",
            "--branch",
            "agent/codex-2/queue-006",
            "--note",
            "Follow bus_message schema",
        ]
    )
    assert rc == 0

    assign_payload = json.loads((assign_dir / "QUEUE-006.json").read_text(encoding="utf-8"))
    assert assign_payload["engineer"] == "codex-2"
    assert assign_payload["plan_id"] == "2025-09-18-task-assign-bus-message"
    assert assign_payload["note"] == "Follow bus_message schema"

    msg_lines = (messages_dir / "QUEUE-006.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(msg_lines) == 1
    message = json.loads(msg_lines[0])
    assert message["type"] == "assignment"
    assert message["summary"] == "Assigned to codex-2"
    assert message["meta"]["assignee"] == "codex-2"
    assert message["meta"]["plan"] == "2025-09-18-task-assign-bus-message"
    assert message["note"] == "Follow bus_message schema"

    tasks_payload = json.loads(tasks_file.read_text(encoding="utf-8"))
    task_entry = next(item for item in tasks_payload["tasks"] if item["id"] == "QUEUE-006")
    assert task_entry["assigned_by"] == "codex-manager"
    assert task_entry["plan_id"] == "2025-09-18-task-assign-bus-message"
    assert task_entry["branch"] == "agent/codex-2/queue-006"

    out = capsys.readouterr().out
    assert "Recorded assignment" in out

    claim_payload = json.loads((claims_dir / "QUEUE-006.json").read_text(encoding="utf-8"))
    assert claim_payload["agent_id"] == "codex-2"
    assert claim_payload.get("plan_id") == "2025-09-18-task-assign-bus-message"
    assert claim_payload["status"] == "active"


def test_task_assign_custom_manager(tmp_path, monkeypatch):
    assign_dir, messages_dir, claims_dir, tasks_file = setup_env(tmp_path, monkeypatch)

    task_assign.main(
        [
            "--task",
            "QUEUE-007",
            "--engineer",
            "codex-4",
            "--manager",
            "codex-lead",
            "--no-auto-claim",
        ]
    )

    message = json.loads((messages_dir / "QUEUE-007.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert message["from"] == "codex-lead"

    tasks_payload = json.loads(tasks_file.read_text(encoding="utf-8"))
    entry = next(item for item in tasks_payload["tasks"] if item["id"] == "QUEUE-007")
    assert entry["assigned_by"] == "codex-lead"

    assert not (claims_dir / "QUEUE-007.json").exists()


def test_task_assign_with_scaffold(tmp_path, monkeypatch, capsys):
    setup_env(tmp_path, monkeypatch)

    rc = task_assign.main(
        [
            "--task",
            "QUEUE-010",
            "--engineer",
            "codex-3",
            "--plan",
            "2025-09-20-receipt-scaffold-v2",
            "--branch",
            "agent/codex-3/queue-010",
            "--scaffold",
        ]
    )
    assert rc == 0

    receipt_dir = tmp_path / "_report" / "agent" / "codex-3" / "2025-09-20-receipt-scaffold-v2"
    assert (receipt_dir / "notes.md").exists()
    summary_payload = json.loads((receipt_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary_payload["plan_id"] == "2025-09-20-receipt-scaffold-v2"
    claim_payload = json.loads((receipt_dir / "claim.json").read_text(encoding="utf-8"))
    assert claim_payload["task_id"] == "QUEUE-010"
    assert claim_payload["agent"] == "codex-3"

    out = capsys.readouterr().out
    assert "Created" in out
