#!/usr/bin/env python3
"""Generate a manager summary of active tasks and receipts."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ASSIGN_DIR = ROOT / "_bus" / "assignments"
CLAIMS_DIR = ROOT / "_bus" / "claims"
MESSAGES_DIR = ROOT / "_bus" / "messages"
REPORT_DIR = ROOT / "_report" / "manager"
TASKS_FILE = ROOT / "agents" / "tasks" / "tasks.json"


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def load_tasks() -> list[dict[str, Any]]:
    data = load_json(TASKS_FILE)
    if isinstance(data, dict) and isinstance(data.get("tasks"), list):
        return data["tasks"]
    return []


def collect_claims() -> dict[str, Any]:
    info: dict[str, Any] = {}
    for path in sorted(CLAIMS_DIR.glob("*.json")):
        info[path.stem] = load_json(path)
    return info


def collect_assignments() -> dict[str, Any]:
    data: dict[str, Any] = {}
    for path in sorted(ASSIGN_DIR.glob("*.json")):
        data[path.stem] = load_json(path)
    return data


def summarize_messages(task_id: str) -> list[str]:
    path = MESSAGES_DIR / f"{task_id}.jsonl"
    if not path.exists():
        return []
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            continue
        ts = msg.get("ts")
        sender = msg.get("from")
        summary = msg.get("summary")
        lines.append(f"- {ts} :: {sender}: {summary}")
    return lines


def write_report(manager_id: str, tasks: list[dict[str, Any]], assignments: dict[str, Any], claims: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = iso_now()
    report_path = REPORT_DIR / f"manager-report-{ts}.md"
    lines = [f"# Manager Report — {ts}", "", f"Manager: `{manager_id}`", ""]

    for task in tasks:
        task_id = task.get("id")
        lines.append(f"## {task_id} — {task.get('title')}")
        lines.append(f"- Role: {task.get('role', 'n/a')} | Priority: {task.get('priority', 'n/a')} | Status: {task.get('status', 'n/a')}")
        if task.get("plan_id"):
            lines.append(f"- Plan: `{task['plan_id']}`")
        if task.get("branch"):
            lines.append(f"- Branch: `{task['branch']}`")
        if task.get("receipts"):
            receipt_list = ', '.join(task.get("receipts", []))
            lines.append(f"- Receipts: {receipt_list}")
        assignment = assignments.get(task_id)
        if assignment:
            lines.append(f"- Assigned to `{assignment.get('engineer')}` at {assignment.get('assigned_at')} (note: {assignment.get('note')})")
        claim = claims.get(task_id)
        if claim:
            lines.append(f"- Current claim: {claim.get('agent_id')} [{claim.get('status')}] → {claim.get('branch')}")
        message_lines = summarize_messages(task_id)
        if message_lines:
            lines.append("- Messages:")
            lines.extend([f"  {msg}" for msg in message_lines])
        if task.get("notes"):
            lines.append(f"- Notes: {task['notes']}")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate manager summary")
    parser.add_argument("--manager", help="Manager agent id")
    args = parser.parse_args(argv)

    manager_id = args.manager or load_json(MANIFEST := ROOT / "AGENT_MANIFEST.json") or {}
    if isinstance(manager_id, dict):
        manager_id = manager_id.get("agent_id", "manager")
    if not isinstance(manager_id, str):
        manager_id = "manager"

    tasks = load_tasks()
    assignments = collect_assignments()
    claims = collect_claims()
    report_path = write_report(manager_id, tasks, assignments, claims)
    print(f"Manager report written to {report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
