from __future__ import annotations

"""Helpers for summarising repository tasks."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from teof._paths import repo_root

ROOT = repo_root(default=Path(__file__).resolve().parents[1])
TASKS_RELATIVE = Path("agents") / "tasks" / "tasks.json"
ASSIGNMENTS_RELATIVE = Path("_bus") / "assignments"
CLAIMS_RELATIVE = Path("_bus") / "claims"

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_STATUS_ORDER = {
    "open": 0,
    "in_progress": 1,
    "active": 1,
    "blocked": 2,
    "review": 3,
    "done": 4,
}


@dataclass
class TaskRecord:
    """Normalized metadata for a backlog task."""

    task_id: str
    title: str
    status: str
    priority: str
    role: str | None
    plan_id: str | None
    notes: str | None
    assigned_by: str | None
    branch: str | None
    receipts: list[str]
    assignment_engineer: str | None
    assignment_manager: str | None
    assignment_note: str | None
    assignment_branch: str | None
    assigned_at: str | None
    claim_agent: str | None
    claim_status: str | None
    claim_branch: str | None
    claim_plan_id: str | None
    claimed_at: str | None
    released_at: str | None


def _load_json(path: Path) -> Mapping[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _normalise_priority(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip().lower()
    return "medium"


def _normalise_status(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip().lower()
    return "open"


def _as_list(value: Any) -> list[str]:
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        results: list[str] = []
        for item in value:
            if isinstance(item, str):
                results.append(item)
        return results
    return []


def _load_tasks(root: Path) -> dict[str, TaskRecord]:
    data = _load_json(root / TASKS_RELATIVE)
    if not data:
        return {}
    tasks_field = data.get("tasks")
    if not isinstance(tasks_field, list):
        return {}
    records: dict[str, TaskRecord] = {}
    for entry in tasks_field:
        if not isinstance(entry, Mapping):
            continue
        task_id = entry.get("id")
        if not isinstance(task_id, str) or not task_id.strip():
            continue
        title = entry.get("title")
        title_str = title.strip() if isinstance(title, str) and title.strip() else task_id
        status = _normalise_status(entry.get("status"))
        priority = _normalise_priority(entry.get("priority"))
        record = TaskRecord(
            task_id=task_id,
            title=title_str,
            status=status,
            priority=priority,
            role=entry.get("role") if isinstance(entry.get("role"), str) else None,
            plan_id=entry.get("plan_id") if isinstance(entry.get("plan_id"), str) else None,
            notes=entry.get("notes") if isinstance(entry.get("notes"), str) else None,
            assigned_by=entry.get("assigned_by") if isinstance(entry.get("assigned_by"), str) else None,
            branch=entry.get("branch") if isinstance(entry.get("branch"), str) else None,
            receipts=_as_list(entry.get("receipts")),
            assignment_engineer=None,
            assignment_manager=None,
            assignment_note=None,
            assignment_branch=None,
            assigned_at=None,
            claim_agent=None,
            claim_status=None,
            claim_branch=None,
            claim_plan_id=None,
            claimed_at=None,
            released_at=None,
        )
        records[task_id] = record
    return records


def _load_assignments(root: Path) -> dict[str, Mapping[str, Any]]:
    directory = root / ASSIGNMENTS_RELATIVE
    if not directory.exists():
        return {}
    data: dict[str, Mapping[str, Any]] = {}
    for path in sorted(directory.glob("*.json")):
        payload = _load_json(path)
        if isinstance(payload, Mapping):
            data[path.stem] = payload
    return data


def _load_claims(root: Path) -> dict[str, Mapping[str, Any]]:
    directory = root / CLAIMS_RELATIVE
    if not directory.exists():
        return {}
    data: dict[str, Mapping[str, Any]] = {}
    for path in sorted(directory.glob("*.json")):
        payload = _load_json(path)
        if isinstance(payload, Mapping):
            data[path.stem] = payload
    return data


def collect_tasks(root: Path | None = None) -> list[TaskRecord]:
    """Return task metadata merged with assignment + claim context."""

    root = root or ROOT
    tasks = _load_tasks(root)
    assignments = _load_assignments(root)
    claims = _load_claims(root)

    # Ensure tasks present for assignments/claims even if missing in tasks.json
    for task_id, payload in assignments.items():
        if task_id not in tasks:
            tasks[task_id] = TaskRecord(
                task_id=task_id,
                title=task_id,
                status="untracked",
                priority="medium",
                role=None,
                plan_id=payload.get("plan_id") if isinstance(payload.get("plan_id"), str) else None,
                notes=None,
                assigned_by=None,
                branch=None,
                receipts=[],
                assignment_engineer=None,
                assignment_manager=None,
                assignment_note=None,
                assignment_branch=None,
                assigned_at=None,
                claim_agent=None,
                claim_status=None,
                claim_branch=None,
                claim_plan_id=None,
                claimed_at=None,
                released_at=None,
            )

    for task_id, payload in claims.items():
        if task_id not in tasks:
            tasks[task_id] = TaskRecord(
                task_id=task_id,
                title=task_id,
                status="untracked",
                priority="medium",
                role=None,
                plan_id=payload.get("plan_id") if isinstance(payload.get("plan_id"), str) else None,
                notes=None,
                assigned_by=None,
                branch=None,
                receipts=[],
                assignment_engineer=None,
                assignment_manager=None,
                assignment_note=None,
                assignment_branch=None,
                assigned_at=None,
                claim_agent=None,
                claim_status=None,
                claim_branch=None,
                claim_plan_id=None,
                claimed_at=None,
                released_at=None,
            )

    for task_id, record in tasks.items():
        assignment = assignments.get(task_id)
        if assignment:
            engineer = assignment.get("engineer")
            manager = assignment.get("manager")
            record.assignment_engineer = engineer if isinstance(engineer, str) else None
            record.assignment_manager = manager if isinstance(manager, str) else None
            record.assignment_note = assignment.get("note") if isinstance(assignment.get("note"), str) else None
            record.assignment_branch = assignment.get("branch") if isinstance(assignment.get("branch"), str) else None
            record.assigned_at = assignment.get("assigned_at") if isinstance(assignment.get("assigned_at"), str) else None
            if not record.plan_id and isinstance(assignment.get("plan_id"), str):
                record.plan_id = assignment["plan_id"]
        claim = claims.get(task_id)
        if claim:
            claim_agent = claim.get("agent_id")
            claim_status = claim.get("status")
            claim_branch = claim.get("branch")
            record.claim_agent = claim_agent if isinstance(claim_agent, str) else None
            record.claim_status = _normalise_status(claim_status)
            record.claim_branch = claim_branch if isinstance(claim_branch, str) else None
            plan_id = claim.get("plan_id")
            if isinstance(plan_id, str):
                record.claim_plan_id = plan_id
                if not record.plan_id:
                    record.plan_id = plan_id
            claimed_at = claim.get("claimed_at")
            released_at = claim.get("released_at")
            record.claimed_at = claimed_at if isinstance(claimed_at, str) else None
            record.released_at = released_at if isinstance(released_at, str) else None
            branch = claim.get("branch")
            if not record.branch and isinstance(branch, str):
                record.branch = branch
            if record.released_at and record.claim_status not in {"done", "released"}:
                record.claim_status = "released"
        if record.claim_status:
            record.claim_status = _normalise_status(record.claim_status)
        record.priority = _normalise_priority(record.priority)
        record.status = _normalise_status(record.status)

    return list(tasks.values())


def filter_open_tasks(tasks: Iterable[TaskRecord], include_done: bool = False) -> list[TaskRecord]:
    results: list[TaskRecord] = []
    for task in tasks:
        if include_done:
            results.append(task)
            continue
        if task.status != "done":
            results.append(task)
    return results


def sort_tasks(tasks: Iterable[TaskRecord]) -> list[TaskRecord]:
    def _order(record: TaskRecord) -> tuple[int, int, str]:
        priority_rank = _PRIORITY_ORDER.get(record.priority, 99)
        status_rank = _STATUS_ORDER.get(record.status, 98)
        return (priority_rank, status_rank, record.task_id)

    return sorted(tasks, key=_order)


def to_payload(tasks: Iterable[TaskRecord], *, warnings: list[str] | None = None) -> dict[str, Any]:
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tasks": [asdict(task) for task in tasks],
    }
    if warnings is not None:
        payload["warnings"] = warnings
    return payload


def render_table(tasks: Iterable[TaskRecord]) -> str:
    rows = []
    for task in tasks:
        claim_desc = "-"
        if task.claim_agent or task.claim_status:
            agent = task.claim_agent or "?"
            status = task.claim_status or "?"
            claim_desc = f"{agent}:{status}"
        row = [
            task.task_id,
            task.status,
            task.priority,
            task.assignment_engineer or "-",
            claim_desc,
            task.plan_id or "-",
            task.title,
        ]
        rows.append(row)

    headers = ["ID", "Status", "Priority", "Assignee", "Claim", "Plan", "Title"]
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    fmt = " ".join(f"{{:<{w}}}" for w in widths)
    lines = [fmt.format(*headers)]
    lines.append("-" * (sum(widths) + len(widths) - 1))
    for row in rows:
        lines.append(fmt.format(*row))
    if not rows:
        lines.append("(no tasks found)")
    return "\n".join(lines)


def compute_warnings(tasks: Iterable[TaskRecord]) -> list[str]:
    warnings: list[str] = []
    active_claim_statuses = {"open", "active", "in_progress", "pending"}
    for task in tasks:
        if task.status == "done" and not task.receipts:
            warnings.append(
                f"{task.task_id}: marked done but no receipts recorded"
            )
        if task.status != "done" and not (task.assignment_engineer or task.claim_agent):
            warnings.append(
                f"{task.task_id}: open with no assignment or active claim"
            )
        if (
            task.assignment_engineer
            and task.claim_agent
            and task.assignment_engineer != task.claim_agent
            and task.claim_status in active_claim_statuses
            and not task.released_at
        ):
            warnings.append(
                f"{task.task_id}: assignment to {task.assignment_engineer} but active claim by {task.claim_agent}"
            )
        if task.claim_status in {"active", "paused"} and not task.claim_agent:
            warnings.append(
                f"{task.task_id}: claim status {task.claim_status} missing agent id"
            )
    return warnings


__all__ = [
    "TaskRecord",
    "collect_tasks",
    "filter_open_tasks",
    "sort_tasks",
    "to_payload",
    "render_table",
    "compute_warnings",
]
