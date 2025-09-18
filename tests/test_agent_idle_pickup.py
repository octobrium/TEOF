import json
from pathlib import Path

import pytest

from tools.agent import idle_pickup, task_assign, bus_claim


def setup_env(tmp_path, monkeypatch):
    assignments_dir = tmp_path / "assignments"
    claims_dir = tmp_path / "claims"
    queue_dir = tmp_path / "queue"
    manifest = tmp_path / "AGENT_MANIFEST.json"

    manifest.write_text(json.dumps({"agent_id": "codex-2"}), encoding="utf-8")

    queue_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(idle_pickup, "ASSIGNMENTS_DIR", assignments_dir)
    monkeypatch.setattr(idle_pickup, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(idle_pickup, "QUEUE_DIR", queue_dir)
    monkeypatch.setattr(idle_pickup, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(idle_pickup, "ROOT", tmp_path)

    monkeypatch.setattr(task_assign, "ASSIGN_DIR", assignments_dir)
    monkeypatch.setattr(task_assign, "MESSAGES_DIR", tmp_path / "messages")
    monkeypatch.setattr(task_assign, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(task_assign, "TASKS_FILE", tmp_path / "tasks" / "tasks.json")
    monkeypatch.setattr(task_assign, "MANIFEST", manifest)
    monkeypatch.setattr(task_assign, "record_usage", lambda *args, **kwargs: None)

    monkeypatch.setattr(bus_claim, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(bus_claim, "ASSIGNMENTS_DIR", assignments_dir)
    monkeypatch.setattr(bus_claim, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(bus_claim, "ROOT", tmp_path)

    (tmp_path / "tasks").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tasks" / "tasks.json").write_text(json.dumps({"tasks": []}), encoding="utf-8")

    return assignments_dir, claims_dir, queue_dir


def write_assignment(assign_dir: Path, task_id: str, engineer=None, plan=None):
    payload = {
        "task_id": task_id,
        "engineer": engineer,
        "manager": "codex-1" if engineer else None,
        "plan_id": plan,
        "status": "active" if engineer else "unassigned",
    }
    assign_dir.mkdir(parents=True, exist_ok=True)
    (assign_dir / f"{task_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def write_claim(claim_dir: Path, task_id: str, agent: str, status: str = "active"):
    claim_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "task_id": task_id,
        "agent_id": agent,
        "branch": f"agent/{agent}/{task_id.lower()}",
        "status": status,
        "claimed_at": "2025-09-18T19:00:00Z",
    }
    (claim_dir / f"{task_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_list_unassigned_tasks(tmp_path, monkeypatch, capsys):
    assignments_dir, claims_dir, queue_dir = setup_env(tmp_path, monkeypatch)
    write_assignment(assignments_dir, "QUEUE-041", None, plan="2025-09-18-test")
    queue_dir.mkdir(parents=True, exist_ok=True)
    (queue_dir / "queue-041.md").write_text("# Task: Test\nSome summary", encoding="utf-8")

    idle_pickup.main(["list"])

    out = capsys.readouterr().out
    assert "QUEUE-041" in out
    assert "(unassigned)" in out


def test_claim_unassigned_auto_assigns(tmp_path, monkeypatch):
    assignments_dir, claims_dir, queue_dir = setup_env(tmp_path, monkeypatch)
    write_assignment(assignments_dir, "QUEUE-042", None, plan="2025-09-18-test")

    idle_pickup.main(["claim", "--task", "QUEUE-042", "--agent", "codex-2"])

    claim_path = claims_dir / "QUEUE-042.json"
    assert claim_path.exists()
    payload = json.loads(claim_path.read_text(encoding="utf-8"))
    assert payload["agent_id"] == "codex-2"


def test_claim_assigned_without_claim(tmp_path, monkeypatch):
    assignments_dir, claims_dir, queue_dir = setup_env(tmp_path, monkeypatch)
    write_assignment(assignments_dir, "QUEUE-043", "codex-2", plan="2025-09-18-test")

    idle_pickup.main(["claim", "--task", "QUEUE-043", "--agent", "codex-2"])

    payload = json.loads((claims_dir / "QUEUE-043.json").read_text(encoding="utf-8"))
    assert payload["agent_id"] == "codex-2"
    assert payload["status"] == "active"


def test_claim_rejects_foreign_assignment(tmp_path, monkeypatch):
    assignments_dir, claims_dir, queue_dir = setup_env(tmp_path, monkeypatch)
    write_assignment(assignments_dir, "QUEUE-044", "codex-3", plan="2025-09-18-test")

    with pytest.raises(SystemExit):
        idle_pickup.main(["claim", "--task", "QUEUE-044", "--agent", "codex-2"])
