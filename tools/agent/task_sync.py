#!/usr/bin/env python3
"""Synchronize tasks.json status with bus claim state."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Tuple

ROOT = Path(__file__).resolve().parents[2]
TASKS_PATH = ROOT / "agents" / "tasks" / "tasks.json"
CLAIMS_DIR = ROOT / "_bus" / "claims"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _claim_status(task_id: str) -> Tuple[str | None, str | None]:
    claim_path = CLAIMS_DIR / f"{task_id}.json"
    if not claim_path.exists():
        return None, None
    try:
        data = _load_json(claim_path)
    except json.JSONDecodeError:
        return None, None
    status = data.get("status")
    agent = data.get("agent_id")
    if isinstance(status, str):
        status = status.lower().strip()
    return status, agent if isinstance(agent, str) else None


def _derive_task_status(claim_status: str | None) -> str | None:
    if not claim_status:
        return None
    if claim_status == "done":
        return "done"
    if claim_status in {"released", "active", "paused"}:
        return "open"
    return None


def sync_tasks(*, dry_run: bool = False) -> list[str]:
    data = _load_json(TASKS_PATH)
    tasks = data.get("tasks", [])
    changes: list[str] = []
    for task in tasks:
        task_id = task.get("id")
        if not isinstance(task_id, str):
            continue
        claim_status, _ = _claim_status(task_id)
        new_status = _derive_task_status(claim_status)
        if not new_status:
            continue
        old_status = task.get("status")
        if old_status != new_status:
            changes.append(f"{task_id}: {old_status} -> {new_status}")
            task["status"] = new_status
    if changes and not dry_run:
        TASKS_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return changes


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synchronize tasks.json status with claim state")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args(argv)
    for change in sync_tasks(dry_run=args.dry_run):
        print(change)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
