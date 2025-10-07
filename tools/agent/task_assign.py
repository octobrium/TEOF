#!/usr/bin/env python3
"""Assign tasks to agents and append bus messages."""
from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from tools.usage.logger import record_usage

from tools.agent import bus_message, bus_claim
from tools.receipts.scaffold import scaffold_claim, format_created, ScaffoldError

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "AGENT_MANIFEST.json"
ASSIGN_DIR = ROOT / "_bus" / "assignments"
MESSAGES_DIR = ROOT / "_bus" / "messages"
CLAIMS_DIR = ROOT / "_bus" / "claims"
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


def append_message(
    task_id: str,
    manager: str,
    engineer: str,
    plan_id: str | None,
    branch: str | None,
    note: str | None,
    manifest_agent: str | None,
) -> Path:
    meta: Dict[str, Any] = {"assignee": engineer}
    if plan_id:
        meta["plan_id"] = plan_id
    temp_manifest_path: Path | None = None
    original_manifest_path = bus_message.MANIFEST_PATH
    try:
        if manifest_agent and manifest_agent != manager:
            tmp_file = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
            try:
                json.dump({"agent_id": manager}, tmp_file)
            finally:
                tmp_file.close()
            temp_manifest_path = Path(tmp_file.name)
            bus_message.MANIFEST_PATH = temp_manifest_path
        message_path = bus_message.log_message(
            task_id=task_id,
            msg_type="assignment",
            summary=f"Assigned to {engineer}",
            agent_id=manager,
            branch=branch,
            plan_id=plan_id,
            meta=meta,
            note=note,
        )
    finally:
        bus_message.MANIFEST_PATH = original_manifest_path
        if temp_manifest_path is not None:
            try:
                temp_manifest_path.unlink()
            except FileNotFoundError:
                pass
    return message_path


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assign tasks via the coordination bus")
    parser.add_argument("--task", required=True, help="Task identifier (e.g., QUEUE-001)")
    parser.add_argument("--engineer", required=True, help="Agent id to assign the task to")
    parser.add_argument("--plan", help="Plan id associated with the task")
    parser.add_argument("--branch", help="Working branch for the assignee")
    parser.add_argument("--manager", help="Manager agent id (defaults to manifest agent_id)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--auto-claim",
        dest="auto_claim",
        action="store_true",
        help="Immediately create a claim for the assigned engineer (default)",
    )
    group.add_argument(
        "--no-auto-claim",
        dest="auto_claim",
        action="store_false",
        help="Skip automatic claim creation",
    )
    parser.set_defaults(auto_claim=True)
    parser.add_argument("--note", help="Optional note to include in assignment message")
    parser.add_argument(
        "--scaffold",
        action="store_true",
        help="Create receipt scaffold for the assigned agent (default: disabled)",
    )
    return parser.parse_args(argv)


def auto_claim(
    task_id: str,
    engineer: str,
    plan_id: str | None,
    branch: str | None,
    *,
    manifest_agent: str | None,
) -> None:
    """Create a claim entry for the assigned engineer."""

    claim_args = [
        "claim",
        "--task",
        task_id,
        "--agent",
        engineer,
    ]
    if plan_id:
        claim_args.extend(["--plan", plan_id])
    if branch:
        claim_args.extend(["--branch", branch])

    # Ensure bus_claim writes into the same claims directory during tests.
    bus_claim.CLAIMS_DIR = CLAIMS_DIR

    original_manifest_path = bus_claim.MANIFEST_PATH
    temp_manifest_path: Path | None = None
    try:
        if manifest_agent and manifest_agent != engineer:
            tmp_file = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
            try:
                json.dump({"agent_id": engineer}, tmp_file)
            finally:
                tmp_file.close()
            temp_manifest_path = Path(tmp_file.name)
            bus_claim.MANIFEST_PATH = temp_manifest_path
        rc = bus_claim.main(claim_args)
    except SystemExit as exc:  # pragma: no cover - passthrough for bus_claim errors
        raise SystemExit(f"auto-claim failed for {task_id}: {exc}") from exc
    finally:
        bus_claim.MANIFEST_PATH = original_manifest_path
        if temp_manifest_path is not None:
            try:
                temp_manifest_path.unlink()
            except FileNotFoundError:
                pass
    if rc != 0:
        raise SystemExit(f"auto-claim failed for {task_id}; exit code {rc}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = load_manifest()
    manifest_agent = manifest.get("agent_id") if isinstance(manifest, dict) else None
    manager = args.manager or manifest_agent or "manager"
    assignment_path = write_assignment(args.task, args.engineer, manager, args.plan, args.branch, args.note)
    message_path = append_message(
        args.task,
        manager,
        args.engineer,
        args.plan,
        args.branch,
        args.note,
        manifest_agent,
    )
    update_tasks(args.task, args.engineer, args.plan, args.branch, manager)

    if args.auto_claim:
        auto_claim(
            args.task,
            args.engineer,
            args.plan,
            args.branch,
            manifest_agent=manifest_agent,
        )

    scaffold_message: str | None = None
    if args.scaffold:
        try:
            result = scaffold_claim(
                task_id=args.task,
                agent=args.engineer,
                plan_id=args.plan,
                branch=args.branch,
            )
        except ScaffoldError as exc:
            raise SystemExit(f"scaffold failed: {exc}") from exc
        scaffold_message = format_created(result.created)
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
    try:
        display_message_path = message_path.relative_to(ROOT)
    except ValueError:
        display_message_path = message_path
    print(f"Logged bus message → {display_message_path}")
    if scaffold_message:
        print(scaffold_message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
