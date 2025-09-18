#!/usr/bin/env python3
"""Assign tasks to agents and append bus messages."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from tools.usage.logger import record_usage

from tools.agent import bus_message

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "AGENT_MANIFEST.json"
ASSIGN_DIR = ROOT / "_bus" / "assignments"
MESSAGES_DIR = ROOT / "_bus" / "messages"
TASKS_FILE = ROOT / "agents" / "tasks" / "tasks.json"


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_manifest() -> dict[str, Any]:
    if not MANIFEST.exists():
        return {}
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def load_tasks() -> dict[str, Any]:
    if not TASKS_FILE.exists():
        return {}
    try:
        return json.loads(TASKS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def update_tasks(task_id: str, engineer: str, plan_id: str | None, branch: str | None, manager: str) -> None:
    data = load_tasks()
    tasks = data.setdefault("tasks", []) if isinstance(data, dict) else []
    for task in tasks:
        if task.get("id") == task_id:
            task["assigned_by"] = manager
            if plan_id:
                task["plan_id"] = plan_id
            if branch:
                task["branch"] = branch
            task.setdefault("role", "engineer")
            task.setdefault("priority", "medium")
            task["status"] = task.get("status", "open")
            break
    else:
        entry = {
            "id": task_id,
            "title": task_id,
            "role": "engineer",
            "priority": "medium",
            "status": "open",
            "plan_id": plan_id,
            "branch": branch,
            "assigned_by": manager,
        }
        tasks.append(entry)
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TASKS_FILE.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_assignment(task_id: str, engineer: str, manager: str, plan_id: str | None, branch: str | None, note: str | None) -> Path:
    ASSIGN_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "task_id": task_id,
        "engineer": engineer,
        "manager": manager,
        "plan_id": plan_id,
        "branch": branch,
        "assigned_at": iso_now(),
        "note": note,
    }
    path = ASSIGN_DIR / f"{task_id}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def append_message(task_id: str, manager: str, engineer: str, plan_id: str | None, branch: str | None, note: str | None) -> None:
    meta: Dict[str, Any] = {"assignee": engineer}
    if plan_id:
        meta.setdefault("plan", plan_id)
    bus_message.log_message(
        task_id=task_id,
        msg_type="assignment",
        summary=f"Assigned to {engineer}",
        agent_id=manager,
        branch=branch,
        plan_id=plan_id,
        meta=meta,
        note=note,
    )


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assign tasks via the coordination bus")
    parser.add_argument("--task", required=True, help="Task identifier (e.g., QUEUE-001)")
    parser.add_argument("--engineer", required=True, help="Agent id to assign the task to")
    parser.add_argument("--plan", help="Plan id associated with the task")
    parser.add_argument("--branch", help="Working branch for the assignee")
    parser.add_argument("--manager", help="Manager agent id (defaults to manifest agent_id)")
    parser.add_argument("--note", help="Optional note to include in assignment message")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = load_manifest()
    manager = args.manager or manifest.get("agent_id") or "manager"
    assignment_path = write_assignment(args.task, args.engineer, manager, args.plan, args.branch, args.note)
    append_message(args.task, manager, args.engineer, args.plan, args.branch, args.note)
    update_tasks(args.task, args.engineer, args.plan, args.branch, manager)
    try:
        display_path = assignment_path.relative_to(ROOT)
    except ValueError:
        display_path = assignment_path
    record_usage(
        "task_assign",
        extra={
            "task": args.task,
            "engineer": args.engineer,
            "manager": manager,
        },
    )
    print(f"Recorded assignment → {display_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
