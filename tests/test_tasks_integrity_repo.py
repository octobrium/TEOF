from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS_FILE = ROOT / "agents" / "tasks" / "tasks.json"


def test_tasks_file_structure() -> None:
    assert TASKS_FILE.exists(), "agents/tasks/tasks.json missing"
    data = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    tasks = data.get("tasks")
    assert isinstance(tasks, list)

    seen_ids: set[str] = set()
    allowed_status = {"open", "done"}
    allowed_priority = {"high", "medium", "low"}

    for entry in tasks:
        assert isinstance(entry, dict)
        task_id = entry.get("id")
        assert isinstance(task_id, str) and task_id.strip(), "task id must be non-empty string"
        assert task_id not in seen_ids, f"duplicate task id {task_id}"
        seen_ids.add(task_id)

        status = entry.get("status")
        assert isinstance(status, str) and status in allowed_status, f"task {task_id} has invalid status {status!r}"

        priority = entry.get("priority")
        if priority is not None:
            assert isinstance(priority, str)
            assert priority in allowed_priority, f"task {task_id} has invalid priority {priority!r}"

        receipts = entry.get("receipts")
        if receipts is not None:
            assert isinstance(receipts, list), f"task {task_id} receipts must be a list"

    assert len(seen_ids) == len(tasks)
