import json
from pathlib import Path

from tools.agent import task_sync


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def test_sync_updates_status(monkeypatch, tmp_path):
    tasks = {
        "tasks": [
            {
                "id": "QUEUE-100",
                "status": "open",
                "branch": "agent/demo/queue-100"
            },
            {
                "id": "QUEUE-200",
                "status": "done",
                "branch": "agent/demo/queue-200"
            }
        ],
        "version": 1
    }
    write(tmp_path / "agents" / "tasks" / "tasks.json", tasks)
    write(
        tmp_path / "_bus" / "claims" / "QUEUE-100.json",
        {
            "task_id": "QUEUE-100",
            "agent_id": "codex-9",
            "status": "done",
            "branch": "agent/demo/queue-100",
            "claimed_at": "2025-09-18T00:00:00Z"
        }
    )
    write(
        tmp_path / "_bus" / "claims" / "QUEUE-200.json",
        {
            "task_id": "QUEUE-200",
            "agent_id": "codex-9",
            "status": "released",
            "branch": "agent/demo/queue-200",
            "claimed_at": "2025-09-18T00:00:00Z"
        }
    )

    monkeypatch.setattr(task_sync, "ROOT", tmp_path)
    monkeypatch.setattr(task_sync, "TASKS_PATH", tmp_path / "agents" / "tasks" / "tasks.json")
    monkeypatch.setattr(task_sync, "CLAIMS_DIR", tmp_path / "_bus" / "claims")

    changes = task_sync.sync_tasks(dry_run=False)

    assert "QUEUE-100: open -> done" in changes
    assert "QUEUE-200: done -> open" in changes

    updated = json.loads((tmp_path / "agents" / "tasks" / "tasks.json").read_text())
    statuses = {t["id"]: t["status"] for t in updated["tasks"]}
    assert statuses["QUEUE-100"] == "done"
    assert statuses["QUEUE-200"] == "open"
