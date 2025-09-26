from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import teof.bootloader as bootloader
from teof import tasks_report


def _setup_repo(root: Path) -> None:
    tasks_dir = root / "agents" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / "tasks.json").write_text(
        json.dumps(
            {
                "version": 1,
                "tasks": [
                    {
                        "id": "QUEUE-100",
                        "title": "Implement tasks CLI",
                        "status": "open",
                        "priority": "high",
                        "role": "engineer",
                        "plan_id": "2025-09-24-teof-tasks",
                        "notes": "Ensure tasks CLI mirrors assignments",
                        "assigned_by": "codex-1",
                        "branch": "agent/codex-9/queue-100",
                        "receipts": ["_report/agent/demo/tasks-cli.json"],
                    },
                    {
                        "id": "QUEUE-101",
                        "title": "Completed task",
                        "status": "done",
                        "priority": "low",
                        "role": "engineer",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    assignments_dir = root / "_bus" / "assignments"
    assignments_dir.mkdir(parents=True, exist_ok=True)
    (assignments_dir / "QUEUE-100.json").write_text(
        json.dumps(
            {
                "task_id": "QUEUE-100",
                "engineer": "codex-9",
                "manager": "codex-1",
                "plan_id": "2025-09-24-teof-tasks",
                "branch": "agent/codex-9/queue-100",
                "note": "Priority for new contributor onboarding",
                "assigned_at": "2025-09-24T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    claims_dir = root / "_bus" / "claims"
    claims_dir.mkdir(parents=True, exist_ok=True)
    (claims_dir / "QUEUE-100.json").write_text(
        json.dumps(
            {
                "task_id": "QUEUE-100",
                "agent_id": "codex-9",
                "status": "active",
                "branch": "agent/codex-9/queue-100",
                "plan_id": "2025-09-24-teof-tasks",
                "claimed_at": "2025-09-24T01:00:00Z",
            }
        ),
        encoding="utf-8",
    )


def test_cli_tasks_json(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(tasks_report, "ROOT", tmp_path)

    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)

    result = bootloader.main(["tasks", "--format", "json"])
    assert result == 0

    payload = json.loads(buffer.getvalue())
    tasks = payload["tasks"]
    assert len(tasks) == 1  # default excludes completed tasks
    record = tasks[0]
    assert record["task_id"] == "QUEUE-100"
    assert record["assignment_engineer"] == "codex-9"
    assert record["claim_agent"] == "codex-9"
    assert record["plan_id"] == "2025-09-24-teof-tasks"
    assert payload["warnings"] == []


def test_cli_tasks_table_includes_done_when_requested(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(tasks_report, "ROOT", tmp_path)

    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)

    result = bootloader.main(["tasks", "--all"])
    assert result == 0
    output = buffer.getvalue()
    assert "QUEUE-100" in output
    assert "QUEUE-101" in output
    assert "Warnings:" in output
    assert "QUEUE-101: marked done but no receipts recorded" in output
