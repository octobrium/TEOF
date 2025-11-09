from __future__ import annotations

"""Helpers for summarising repository tasks."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from collections import Counter

from teof._paths import repo_root
from tools.autonomy import receipt_utils

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


def _resolve_receipts(task_id: str, entry: Mapping[str, Any] | None) -> list[str]:
    """Resolve receipts (plan/guard/manual) for a task-like entry."""

    if entry is None:
        entry = {}
    manual_receipts = _as_list(entry.get("receipts"))
    payload: dict[str, Any] = {"id": task_id}
    if manual_receipts:
        payload["receipts"] = manual_receipts
    receipts_ref = entry.get("receipts_ref") if isinstance(entry, Mapping) else None
    plan_id = entry.get("plan_id") if isinstance(entry, Mapping) else None
    if not isinstance(receipts_ref, Mapping) and isinstance(plan_id, str) and plan_id.strip():
        receipts_ref = {"kind": "plan", "plan_id": plan_id}
    if isinstance(receipts_ref, Mapping):
        payload["receipts_ref"] = receipts_ref
    try:
        resolved = receipt_utils.resolve_item_receipts(payload)
    except (FileNotFoundError, ValueError):
        resolved = manual_receipts
    return resolved


def _normalise_tokens(values: Sequence[str] | None) -> set[str]:
    tokens: set[str] = set()
    if not values:
        return tokens
    for value in values:
        if not isinstance(value, str):
            continue
        token = value.strip().lower()
        if token:
            tokens.add(token)
    return tokens


def _record_agents(record: TaskRecord) -> set[str]:
    candidates = [
        record.assignment_engineer,
        record.claim_agent,
    ]
    normalized: set[str] = set()
    for entry in candidates:
        if isinstance(entry, str):
            token = entry.strip().lower()
            if token:
                normalized.add(token)
    return normalized


def _record_plans(record: TaskRecord) -> set[str]:
    candidates = [
        record.plan_id,
        record.claim_plan_id,
    ]
    tokens: set[str] = set()
    for entry in candidates:
        if isinstance(entry, str):
            token = entry.strip().lower()
            if token:
                tokens.add(token)
    return tokens


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
            receipts=_resolve_receipts(task_id, entry),
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
    tracked_task_ids = set(tasks.keys())
    assignments = _load_assignments(root)
    claims = _load_claims(root)

    # Ensure tasks present for assignments/claims even if missing in tasks.json
    for task_id, payload in assignments.items():
        if task_id not in tasks:
            status = _normalise_status(payload.get("status") or "open")
            tasks[task_id] = TaskRecord(
                task_id=task_id,
                title=task_id,
                status=status,
                priority=_normalise_priority(payload.get("priority")),
                role=None,
                plan_id=payload.get("plan_id") if isinstance(payload.get("plan_id"), str) else None,
                notes=None,
                assigned_by=None,
                branch=None,
                receipts=_resolve_receipts(task_id, payload),
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
            status = _normalise_status(payload.get("status") or "open")
            tasks[task_id] = TaskRecord(
                task_id=task_id,
                title=task_id,
                status=status,
                priority=_normalise_priority(payload.get("priority")),
                role=None,
                plan_id=payload.get("plan_id") if isinstance(payload.get("plan_id"), str) else None,
                notes=None,
                assigned_by=None,
                branch=None,
                receipts=_resolve_receipts(task_id, payload),
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
            claim_status_norm = _normalise_status(claim_status)
            record.claim_status = claim_status_norm
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
            if (
                task_id not in tracked_task_ids
                and claim_status_norm
                and claim_status_norm not in {"done", "released"}
            ):
                record.status = claim_status_norm
            if record.released_at and record.claim_status not in {"done", "released"}:
                record.claim_status = "released"
        if record.claim_status:
            record.claim_status = _normalise_status(record.claim_status)
        record.priority = _normalise_priority(record.priority)
        record.status = _normalise_status(record.status)

    return list(tasks.values())


def filter_open_tasks(
    tasks: Iterable[TaskRecord],
    include_done: bool = False,
    *,
    statuses: Sequence[str] | None = None,
    priorities: Sequence[str] | None = None,
    agents: Sequence[str] | None = None,
    plans: Sequence[str] | None = None,
) -> list[TaskRecord]:
    """Filter tasks using normalized status/priority/agent selectors."""

    status_filter = _normalise_tokens(statuses)
    priority_filter = _normalise_tokens(priorities)
    agent_filter = _normalise_tokens(agents)
    plan_filter = _normalise_tokens(plans)

    results: list[TaskRecord] = []
    for task in tasks:
        if not include_done and task.status == "done":
            continue
        if status_filter and task.status not in status_filter:
            continue
        if priority_filter and task.priority not in priority_filter:
            continue
        if agent_filter:
            if not _record_agents(task).intersection(agent_filter):
                continue
        if plan_filter and not _record_plans(task).intersection(plan_filter):
            continue
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
            warnings.append(f"{task.task_id}: marked done but no receipts recorded")
        if task.status != "done" and not (task.assignment_engineer or task.claim_agent):
            warnings.append(f"{task.task_id}: open with no assignment or active claim")
        if task.status != "done" and not task.plan_id:
            warnings.append(f"{task.task_id}: open task missing plan_id linkage")
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


def summarize_tasks(tasks: Iterable[TaskRecord]) -> dict[str, object]:
    records = list(tasks)
    status_counts = Counter(record.status for record in records)
    priority_counts = Counter(record.priority for record in records)
    summary = {
        "total": len(records),
        "status": dict(status_counts),
        "priority": dict(priority_counts),
        "assignments": sum(1 for record in records if record.assignment_engineer),
        "claims": sum(1 for record in records if record.claim_agent),
        "open_unowned": sum(
            1
            for record in records
            if record.status != "done" and not (record.assignment_engineer or record.claim_agent)
        ),
    }
    return summary


__all__ = [
    "TaskRecord",
    "collect_tasks",
    "filter_open_tasks",
    "sort_tasks",
    "to_payload",
    "render_table",
    "compute_warnings",
    "summarize_tasks",
]
