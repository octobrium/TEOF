#!/usr/bin/env python3
"""Generate a coordination dashboard aggregating plans, claims, and heartbeats."""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from tools.usage.logger import record_usage
from tools.planner import queue_warnings as planner_queue_warnings

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
ROOT = Path(__file__).resolve().parents[2]
PLANS_DIRNAME = "_plans"
CLAIMS_DIRNAME = "_bus/claims"
EVENT_LOG = "_bus/events/events.jsonl"
MANAGER_MESSAGES = "_bus/messages/manager-report.jsonl"
ASSIGN_DIRNAME = "_bus/assignments"
SESSION_DIRNAME = "_report/session"
DIRTY_HANDOFF_SUBDIR = "dirty-handoff"
DEFAULT_MANAGER_WINDOW_MINUTES = 30.0
DEFAULT_AGENT_WINDOW_MINUTES = 60.0
DEFAULT_DIRECTIVE_LIMIT = 10

# Personas moved out of rotation should live here until their manifests/plans
# disappear entirely. This keeps historical events from forcing perpetual
# heartbeat alerts.
RETIRED_AGENTS = {"codex-observer"}

DISPLAY_ALIASES = {
    "Octo": "Octo",
    "template": "template (sample)",
}


def _is_retired(agent_id: str | None) -> bool:
    return bool(agent_id) and agent_id in RETIRED_AGENTS


def _display_actor(value: str | None) -> str:
    if not value:
        return "—"
    return DISPLAY_ALIASES.get(value, value)


def _format_alert(message: str) -> str:
    formatted = message
    for raw, pretty in DISPLAY_ALIASES.items():
        formatted = formatted.replace(f"actor={raw}", f"actor={pretty}")
        formatted = formatted.replace(f"Heartbeat {raw}", f"Heartbeat {pretty}")
    return formatted


class DashboardError(RuntimeError):
    """Raised when dashboard generation fails."""


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utcnow().strftime(ISO_FMT)


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise DashboardError(f"JSON source missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DashboardError(f"Invalid JSON in {path}: {exc}") from exc


def _optional_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.strptime(ts, ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


@dataclass
class PlanSummary:
    plan_id: str
    actor: str | None
    status: str | None
    steps_total: int
    steps_completed: int
    pending_steps: list[str]
    checkpoint_status: str | None
    missing_receipts: bool
    missing_details: list[str]

    def to_payload(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "actor": self.actor,
            "status": self.status,
            "steps_total": self.steps_total,
            "steps_completed": self.steps_completed,
            "pending_steps": self.pending_steps,
            "checkpoint_status": self.checkpoint_status,
            "missing_receipts": self.missing_receipts,
            "missing_details": self.missing_details,
        }


@dataclass
class ClaimSummary:
    task_id: str
    agent_id: str | None
    status: str | None
    branch: str | None
    plan_id: str | None
    claimed_at: str | None
    released_at: str | None

    def to_payload(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "status": self.status,
            "branch": self.branch,
            "plan_id": self.plan_id,
            "claimed_at": self.claimed_at,
            "released_at": self.released_at,
        }


@dataclass
class HeartbeatRecord:
    agent_id: str
    last_seen: str | None
    state: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "last_seen": self.last_seen,
            "state": self.state,
        }


@dataclass
class DirectiveRecord:
    ts: str
    sender: str | None
    summary: str | None
    type: str | None

    def to_payload(self) -> dict[str, Any]:
        return {
            "ts": self.ts,
            "from": self.sender,
            "summary": self.summary,
            "type": self.type,
        }


def _iter_plan_paths(root: Path) -> Iterable[Path]:
    plans_dir = root / PLANS_DIRNAME
    if not plans_dir.exists():
        return []
    return sorted(plans_dir.glob("*.plan.json"))


def _parse_dirty_receipt(path: Path) -> tuple[str | None, list[str]]:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return None, []
    captured_at: str | None = None
    preview: list[str] = []
    for line in content.splitlines():
        if line.startswith("#"):
            if line.startswith("# captured_at="):
                captured_at = line.partition("=")[2].strip() or None
            continue
        stripped = line.strip()
        if stripped:
            preview.append(stripped)
    return captured_at, preview[:5]


def _collect_plan_summary(root: Path) -> list[PlanSummary]:
    summaries: list[PlanSummary] = []
    for path in _iter_plan_paths(root):
        try:
            data = _read_json(path)
        except DashboardError:
            continue
        if not isinstance(data, dict):
            continue
        plan_id = data.get("plan_id", path.stem)
        status = (data.get("status") or "").lower() or None
        if status in {"done", "completed", "closed"}:
            continue
        actor = data.get("actor")
        steps = data.get("steps")
        if not isinstance(steps, list):
            steps = []
        steps_total = len(steps)
        steps_completed = 0
        pending_steps: list[str] = []
        missing_details: list[str] = []

        def _validate_receipts(source: str, receipts: Any) -> None:
            paths = []
            if isinstance(receipts, list):
                for entry in receipts:
                    if isinstance(entry, str):
                        paths.append(entry)
            elif isinstance(receipts, str):
                paths.append(receipts)
            if not paths:
                missing_details.append(f"{source}: no receipts recorded")
                return
            for rel in paths:
                candidate = (root / rel).resolve()
                if not candidate.exists():
                    missing_details.append(f"{source}: missing {rel}")

        for step in steps:
            if not isinstance(step, dict):
                continue
            step_id = step.get("id") or "?"
            step_status = (step.get("status") or "").lower()
            if step_status in {"completed", "done"}:
                steps_completed += 1
                _validate_receipts(f"{plan_id}:{step_id}", step.get("receipts"))
            else:
                pending_steps.append(step_id)
        checkpoint = data.get("checkpoint")
        checkpoint_status = None
        if isinstance(checkpoint, dict):
            checkpoint_status = checkpoint.get("status") or checkpoint.get("state")
            if (checkpoint.get("status") or "").lower() in {"completed", "done"}:
                _validate_receipts(f"{plan_id}:checkpoint", checkpoint.get("receipts"))
        plan_receipts = data.get("receipts")
        if plan_receipts:
            _validate_receipts(f"{plan_id}:plan", plan_receipts)
        missing_receipts = bool(missing_details)
        summaries.append(
            PlanSummary(
                plan_id=str(plan_id),
                actor=str(actor) if actor else None,
                status=status,
                steps_total=steps_total,
                steps_completed=steps_completed,
                pending_steps=pending_steps,
                checkpoint_status=checkpoint_status,
                missing_receipts=missing_receipts,
                missing_details=sorted(set(missing_details)),
            )
        )
    summaries.sort(key=lambda item: item.plan_id)
    return summaries


def _collect_claims(root: Path) -> list[ClaimSummary]:
    claims_dir = root / CLAIMS_DIRNAME
    if not claims_dir.exists():
        return []
    summaries: list[ClaimSummary] = []
    for path in sorted(claims_dir.glob("*.json")):
        data = _optional_json(path)
        if not isinstance(data, dict):
            continue
        summaries.append(
            ClaimSummary(
                task_id=path.stem,
                agent_id=data.get("agent_id"),
                status=data.get("status"),
                branch=data.get("branch"),
                plan_id=data.get("plan_id"),
                claimed_at=data.get("claimed_at") or data.get("claimed"),
                released_at=data.get("released_at"),
            )
        )
    summaries.sort(key=lambda item: item.task_id)
    return summaries


def _identify_unclaimed_plans(
    plans: list[PlanSummary],
    claims: list[ClaimSummary],
) -> list[PlanSummary]:
    """Return active plans that currently lack an open claim."""

    active_claims: set[str] = set()
    for claim in claims:
        status = (claim.status or "").lower()
        if status in {"done", "completed", "closed"}:
            continue
        if claim.plan_id:
            active_claims.add(claim.plan_id)

    unclaimed: list[PlanSummary] = []
    for plan in plans:
        status = (plan.status or "").lower()
        if status in {"done", "completed", "closed"}:
            continue
        if plan.plan_id not in active_claims:
            unclaimed.append(plan)
    return unclaimed


def _collect_pruning_candidates(root: Path) -> dict[str, list[dict[str, str]]]:
    """Inventory plan/claim files that are already marked complete."""

    plans: list[dict[str, str]] = []
    claims: list[dict[str, str]] = []

    plans_dir = root / PLANS_DIRNAME
    if plans_dir.exists():
        for path in sorted(plans_dir.glob("*.plan.json")):
            payload = _optional_json(path)
            if not isinstance(payload, dict):
                continue
            status = (payload.get("status") or "").lower()
            if status in {"done", "completed", "closed"}:
                plans.append(
                    {
                        "plan_id": str(payload.get("plan_id", path.stem)),
                        "status": status or "done",
                        "path": str(path.relative_to(root)),
                    }
                )

    claims_dir = root / CLAIMS_DIRNAME
    if claims_dir.exists():
        for path in sorted(claims_dir.glob("*.json")):
            payload = _optional_json(path)
            if not isinstance(payload, dict):
                continue
            status = (payload.get("status") or "").lower()
            if status in {"done", "completed", "closed"}:
                claims.append(
                    {
                        "task_id": path.stem,
                        "status": status or "done",
                        "path": str(path.relative_to(root)),
                    }
                )

    return {
        "plans": plans,
        "claims": claims,
    }


def _collect_manager_candidates(root: Path) -> set[str]:
    managers: set[str] = set()
    for path in root.glob("AGENT_MANIFEST*.json"):
        data = _optional_json(path)
        if not isinstance(data, dict):
            continue
        agent_id = data.get("agent_id")
        if not isinstance(agent_id, str):
            continue
        desired = data.get("desired_roles") or []
        if isinstance(desired, list) and any(role == "manager" for role in desired):
            managers.add(agent_id)
    assign_dir = root / ASSIGN_DIRNAME
    if assign_dir.exists():
        for path in assign_dir.glob("*.json"):
            data = _optional_json(path)
            if isinstance(data, dict):
                manager = data.get("manager")
                if isinstance(manager, str) and manager:
                    managers.add(manager)
    return managers


def _collect_dirty_handoffs(root: Path) -> list[dict[str, Any]]:
    session_root = root / SESSION_DIRNAME
    if not session_root.exists():
        return []
    latest: dict[str, dict[str, Any]] = {}
    pending_counts: dict[str, int] = {}
    for agent_dir in sorted(session_root.iterdir()):
        if not agent_dir.is_dir():
            continue
        agent_id = agent_dir.name
        if _is_retired(agent_id):
            continue
        handoff_dir = agent_dir / DIRTY_HANDOFF_SUBDIR
        if not handoff_dir.exists():
            continue
        for receipt_path in sorted(handoff_dir.glob("*.txt")):
            pending_counts[agent_id] = pending_counts.get(agent_id, 0) + 1
            captured_at, preview = _parse_dirty_receipt(receipt_path)
            if not captured_at:
                ts = datetime.fromtimestamp(receipt_path.stat().st_mtime, tz=timezone.utc)
                captured_at = ts.strftime(ISO_FMT)
            current = latest.get(agent_id)
            current_key = current.get("captured_at") if current else ""
            candidate_key = captured_at or ""
            if current is None or candidate_key > current_key:
                try:
                    rel_path = receipt_path.relative_to(root)
                    receipt_value = rel_path.as_posix()
                except ValueError:
                    receipt_value = receipt_path.as_posix()
                latest[agent_id] = {
                    "agent_id": agent_id,
                    "captured_at": captured_at,
                    "receipt": receipt_value,
                    "status_preview": preview,
                }
    for agent_id, count in pending_counts.items():
        if agent_id in latest:
            latest[agent_id]["pending_count"] = count
    return [latest[key] for key in sorted(latest)]


def _collect_events(root: Path) -> list[dict[str, Any]]:
    path = root / EVENT_LOG
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        events.append(entry)
    return events


def _build_last_seen(events: Iterable[dict[str, Any]]) -> dict[str, datetime]:
    last_seen: dict[str, datetime] = {}
    for entry in events:
        agent = entry.get("agent_id")
        if not isinstance(agent, str):
            continue
        event_type = entry.get("event")
        if event_type not in {"handshake", "status"}:
            continue
        ts = _parse_iso(entry.get("ts"))
        if ts is None:
            continue
        last_seen[agent] = ts
    return last_seen


def _determine_state(ts: datetime | None, window_minutes: float | None, now: datetime) -> str:
    if ts is None:
        return "missing"
    if window_minutes is not None and window_minutes > 0:
        threshold = timedelta(minutes=window_minutes)
        if now - ts > threshold:
            return "stale"
    return "active"


def _collect_agent_candidates(plans: list[PlanSummary], claims: list[ClaimSummary], events: list[dict[str, Any]]) -> set[str]:
    agents: set[str] = set()
    for plan in plans:
        if plan.actor and not _is_retired(plan.actor):
            agents.add(plan.actor)
    for claim in claims:
        if claim.agent_id and not _is_retired(claim.agent_id):
            agents.add(claim.agent_id)
    for entry in events:
        agent = entry.get("agent_id")
        if isinstance(agent, str) and not _is_retired(agent):
            agents.add(agent)
    return agents


def _collect_heartbeats(
    root: Path,
    plans: list[PlanSummary],
    claims: list[ClaimSummary],
    *,
    manager_window: float,
    agent_window: float,
) -> dict[str, list[HeartbeatRecord]]:
    events = _collect_events(root)
    last_seen = _build_last_seen(events)
    now = utcnow()
    managers = _collect_manager_candidates(root)
    manager_records: list[HeartbeatRecord] = []
    for agent_id in sorted(managers):
        if _is_retired(agent_id):
            continue
        ts = last_seen.get(agent_id)
        manager_records.append(
            HeartbeatRecord(
                agent_id=agent_id,
                last_seen=ts.strftime(ISO_FMT) if ts else None,
                state=_determine_state(ts, manager_window, now),
            )
        )
    agent_candidates = _collect_agent_candidates(plans, claims, events)
    agent_records: list[HeartbeatRecord] = []
    for agent_id in sorted(agent_candidates):
        if _is_retired(agent_id):
            continue
        ts = last_seen.get(agent_id)
        agent_records.append(
            HeartbeatRecord(
                agent_id=agent_id,
                last_seen=ts.strftime(ISO_FMT) if ts else None,
                state=_determine_state(ts, agent_window, now),
            )
        )
    return {
        "managers": manager_records,
        "agents": agent_records,
    }


def _collect_directives(root: Path, limit: int) -> list[DirectiveRecord]:
    path = root / MANAGER_MESSAGES
    if not path.exists():
        return []
    records: list[DirectiveRecord] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        ts = entry.get("ts")
        if not isinstance(ts, str):
            continue
        records.append(
            DirectiveRecord(
                ts=ts,
                sender=entry.get("from"),
                summary=entry.get("summary"),
                type=entry.get("type"),
            )
        )
    records.sort(key=lambda item: item.ts, reverse=True)
    if limit >= 0:
        records = records[:limit]
    records.sort(key=lambda item: item.ts)
    return records


def _build_alerts(
    plans: list[PlanSummary],
    heartbeats: dict[str, list[HeartbeatRecord]],
    unclaimed_plans: list[PlanSummary],
    dirty_handoffs: list[dict[str, Any]],
) -> list[str]:
    alerts: list[str] = []
    seen: set[str] = set()
    for plan in plans:
        if plan.missing_receipts:
            details = ", ".join(plan.missing_details) if plan.missing_details else "missing receipts"
            message = f"Plan {plan.plan_id}: {details}"
            if message not in seen:
                alerts.append(message)
                seen.add(message)
    for plan in unclaimed_plans:
        actor = plan.actor or "unknown"
        message = f"Plan {plan.plan_id} has no active claim (actor={actor})"
        if message not in seen:
            alerts.append(message)
            seen.add(message)
    for record in heartbeats.get("managers", []) + heartbeats.get("agents", []):
        if record.state != "active":
            message = f"Heartbeat {record.agent_id} is {record.state}"
            if message not in seen:
                alerts.append(message)
                seen.add(message)
    for record in dirty_handoffs:
        agent = record.get("agent_id", "unknown")
        receipt = record.get("receipt", "-")
        message = f"Dirty handoff pending for {agent} (receipt={receipt})"
        if message not in seen:
            alerts.append(message)
            seen.add(message)
    return alerts


def _collect_heartbeat_initiatives(plans: list[PlanSummary]) -> list[dict[str, Any]]:
    """Summarize active heartbeat-focused plans for quick reference."""

    initiatives: list[dict[str, Any]] = []
    for plan in plans:
        if "heartbeat" not in plan.plan_id.lower():
            continue
        initiatives.append(
            {
                "plan_id": plan.plan_id,
                "actor": plan.actor,
                "status": plan.status,
                "pending_steps": list(plan.pending_steps),
            }
        )
    return initiatives


def _render_heartbeat_notes(meta: dict[str, Any], *, prefix: str = "") -> list[str]:
    """Produce explanatory lines about heartbeat automation for markdown output."""

    if not meta:
        return []

    lines: list[str] = []
    manager_window = meta.get("manager_window_minutes")
    agent_window = meta.get("agent_window_minutes")
    window_parts: list[str] = []
    if manager_window is not None:
        window_parts.append(f"managers: {manager_window:g}m")
    if agent_window is not None:
        window_parts.append(f"agents: {agent_window:g}m")
    if window_parts:
        lines.append(f"{prefix}Heartbeat windows — " + ", ".join(window_parts) + ".")

    automation = meta.get("automation_plans") or []
    if automation:
        lines.append(f"{prefix}Heartbeat automation in flight:")
        for item in automation:
            actor = _display_actor(item.get("actor"))
            status = item.get("status") or "queued"
            pending = ", ".join(item.get("pending_steps") or []) or "none"
            lines.append(
                f"{prefix}- {item.get('plan_id', '?')}: {actor} (status={status}; pending={pending})"
            )
    return lines


def build_dashboard(
    root: Path,
    *,
    manager_window: float,
    agent_window: float,
    directive_limit: int,
) -> dict[str, Any]:
    plans = _collect_plan_summary(root)
    claims = _collect_claims(root)
    unclaimed_plans = _identify_unclaimed_plans(plans, claims)
    heartbeats = _collect_heartbeats(
        root,
        plans,
        claims,
        manager_window=manager_window,
        agent_window=agent_window,
    )
    directives = _collect_directives(root, directive_limit)
    pruning = _collect_pruning_candidates(root)
    dirty_handoffs = _collect_dirty_handoffs(root)
    alerts = _build_alerts(plans, heartbeats, unclaimed_plans, dirty_handoffs)
    queue_warnings = planner_queue_warnings.load_queue_warnings(root)
    for warning in queue_warnings:
        message = warning.get("message")
        if isinstance(message, str) and message:
            formatted = f"Queue warning: {message}"
            if formatted not in alerts:
                alerts.append(formatted)
    heartbeat_meta = {
        "manager_window_minutes": manager_window,
        "agent_window_minutes": agent_window,
        "automation_plans": _collect_heartbeat_initiatives(plans),
    }
    return {
        "generated_at": iso_now(),
        "plans": [plan.to_payload() for plan in plans],
        "claims": [claim.to_payload() for claim in claims],
        "heartbeats": {
            "managers": [record.to_payload() for record in heartbeats.get("managers", [])],
            "agents": [record.to_payload() for record in heartbeats.get("agents", [])],
        },
        "manager_directives": [record.to_payload() for record in directives],
        "alerts": alerts,
        "unclaimed_plans": [plan.to_payload() for plan in unclaimed_plans],
        "pruning_candidates": pruning,
        "heartbeat_meta": heartbeat_meta,
        "dirty_handoffs": dirty_handoffs,
        "planner_queue_warnings": queue_warnings,
    }


def _format_row(values: Iterable[str]) -> str:
    return " | ".join(values)


def _render_table(headers: Sequence[str], rows: Iterable[Sequence[str]]) -> list[str]:
    widths = [len(header) for header in headers]
    materialized = []
    for row in rows:
        materialized.append([str(cell) for cell in row])
        for idx, cell in enumerate(materialized[-1]):
            widths[idx] = max(widths[idx], len(cell))
    header_line = _format_row(header.ljust(widths[idx]) for idx, header in enumerate(headers))
    divider = _format_row("-" * widths[idx] for idx in range(len(headers)))
    lines = [header_line, divider]
    for row in materialized:
        lines.append(_format_row(cell.ljust(widths[idx]) for idx, cell in enumerate(row)))
    return lines


def render_markdown(data: dict[str, Any], *, compact: bool = False) -> str:
    generated_at = data.get("generated_at", iso_now())
    if compact:
        lines: list[str] = [f"# Coordination Dashboard — {generated_at}", ""]

        plans = data.get("plans", [])
        lines.append("## Active Work")
        if plans:
            rows = []
            for plan in plans:
                rows.append(
                    (
                        _display_actor(plan.get("actor")),
                        plan.get("plan_id", "-"),
                        plan.get("status", "-"),
                        f"{plan.get('steps_completed', 0)}/{plan.get('steps_total', 0)}",
                        ",".join(plan.get("pending_steps") or []) or "—",
                        "yes" if plan.get("missing_receipts") else "no",
                    )
                )
            lines.extend(
                _render_table(
                    ("agent", "plan", "status", "steps", "pending", "missing_receipts"),
                    rows,
                )
            )
        else:
            lines.append("No active plans.")
        lines.append("")

        unclaimed = data.get("unclaimed_plans", [])
        lines.append("## Unclaimed Plans")
        if unclaimed:
            rows = []
            for plan in unclaimed:
                rows.append(
                    (
                        _display_actor(plan.get("actor")),
                        plan.get("plan_id", "-"),
                        plan.get("status", "-"),
                        ",".join(plan.get("pending_steps") or []) or "—",
                    )
                )
            lines.extend(_render_table(("actor", "plan", "status", "pending"), rows))
        else:
            lines.append("None")
        lines.append("")

        dirty = data.get("dirty_handoffs", [])
        lines.append("## Dirty Handoffs")
        if dirty:
            for record in dirty:
                agent = record.get("agent_id", "-")
                captured = record.get("captured_at", "-")
                receipt = record.get("receipt", "-")
                lines.append(f"- {agent}: {captured} ({receipt})")
        else:
            lines.append("- none")
        lines.append("")

        alerts = data.get("alerts", [])
        lines.append("## Alerts")
        if alerts:
            for alert in alerts:
                lines.append(f"- {_format_alert(alert)}")
        else:
            lines.append("- none")
        warnings = data.get("planner_queue_warnings", [])
        lines.append("")
        lines.append("## Planner Queue Warnings")
        if warnings:
            for warning in warnings:
                message = warning.get("message") if isinstance(warning, dict) else str(warning)
                lines.append(f"- {message}")
        else:
            lines.append("- none")

        return "\n".join(lines)

    lines: list[str] = [f"# Coordination Dashboard — {generated_at}", ""]

    plans = data.get("plans", [])
    lines.append("## Active Plans")
    if plans:
        table_rows = []
        for plan in plans:
            table_rows.append(
                (
                    plan.get("plan_id", "?"),
                    _display_actor(plan.get("actor")),
                    plan.get("status", "-"),
                    f"{plan.get('steps_completed', 0)}/{plan.get('steps_total', 0)}",
                    "; ".join(plan.get("pending_steps", [])) or "-",
                    "yes" if plan.get("missing_receipts") else "no",
                )
            )
        lines.extend(
            _render_table(
                ("plan", "actor", "status", "steps", "pending", "missing_receipts"),
                table_rows,
            )
        )
    else:
        lines.append("No active plans.")
    lines.append("")

    claims = data.get("claims", [])
    lines.append("## Claims")
    if claims:
        rows = []
        for claim in claims:
            rows.append(
                (
                    claim.get("task_id", "?"),
                    claim.get("agent_id", "-"),
                    claim.get("status", "-"),
                    claim.get("plan_id", "-"),
                    claim.get("branch", "-"),
                )
            )
        lines.extend(
            _render_table(
                ("task", "agent", "status", "plan", "branch"),
                rows,
            )
        )
    else:
        lines.append("No claims found.")
    lines.append("")

    lines.append("## Unclaimed Plans")
    unclaimed = data.get("unclaimed_plans", [])
    if unclaimed:
        rows = []
        for entry in unclaimed:
            pending = entry.get("pending_steps") or []
            rows.append(
                (
                    entry.get("plan_id", "-"),
                    _display_actor(entry.get("actor")),
                    entry.get("status", "-"),
                    ",".join(pending) if pending else "-",
                )
            )
        lines.extend(_render_table(("plan", "actor", "status", "pending"), rows))
    else:
        lines.append("No active plans without claims.")
    lines.append("")

    lines.append("## Dirty Handoffs")
    dirty = data.get("dirty_handoffs", [])
    if dirty:
        rows = []
        for record in dirty:
            preview = "; ".join(record.get("status_preview", [])) or "-"
            rows.append(
                (
                    record.get("agent_id", "-"),
                    record.get("captured_at", "-"),
                    record.get("receipt", "-"),
                    preview,
                )
            )
        lines.extend(_render_table(("agent", "captured", "receipt", "preview"), rows))
        counts = [
            f"{record.get('agent_id', '-')}: {record.get('pending_count', 1)} receipt(s)"
            for record in dirty
            if record.get("pending_count")
        ]
        if counts:
            lines.append("Outstanding dirty receipts: " + "; ".join(counts))
        lines.append("")
    else:
        lines.append("No dirty handoffs detected.")
        lines.append("")

    lines.append("## Heartbeats")
    heartbeat_meta = data.get("heartbeat_meta", {})
    note_lines = _render_heartbeat_notes(heartbeat_meta)
    if note_lines:
        lines.extend(note_lines)
        lines.append("")
    lines.append("### Managers")
    managers = data.get("heartbeats", {}).get("managers", [])
    if managers:
        rows = []
        for record in managers:
            rows.append((record.get("agent_id", "-"), record.get("state", "-"), record.get("last_seen", "-")))
        lines.extend(_render_table(("agent", "state", "last_seen"), rows))
    else:
        lines.append("No manager heartbeats.")
    lines.append("")

    lines.append("### Agents")
    agents = data.get("heartbeats", {}).get("agents", [])
    if agents:
        rows = []
        for record in agents:
            rows.append((record.get("agent_id", "-"), record.get("state", "-"), record.get("last_seen", "-")))
        lines.extend(_render_table(("agent", "state", "last_seen"), rows))
    else:
        lines.append("No agent heartbeats.")
    lines.append("")

    directives = data.get("manager_directives", [])
    lines.append("## Manager Directives")
    if directives:
        for entry in directives:
            summary = entry.get("summary", "(no summary)")
            sender = entry.get("from", "unknown")
            ts = entry.get("ts", "?")
            dtype = entry.get("type") or "note"
            lines.append(f"- {ts} :: {sender} [{dtype}] — {summary}")
    else:
        lines.append("No manager directives in window.")
    lines.append("")

    alerts = data.get("alerts", [])
    lines.append("## Alerts")
    if alerts:
        for alert in alerts:
            lines.append(f"- {_format_alert(alert)}")
    else:
        lines.append("- none")
    warnings = data.get("planner_queue_warnings", [])
    lines.append("")
    lines.append("## Planner Queue Warnings")
    if warnings:
        rows = []
        for warning in warnings:
            if isinstance(warning, dict):
                rows.append(
                    (
                        warning.get("plan_id", "-"),
                        warning.get("queue_ref", "-"),
                        warning.get("issue", "-"),
                        warning.get("message", "-"),
                    )
                )
            else:
                rows.append(("-", "-", "-", str(warning)))
        lines.extend(
            _render_table(("plan", "queue", "issue", "message"), rows)
        )
    else:
        lines.append("No queue warnings detected.")

    return "\n".join(lines)


def write_output(content: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content + "\n", encoding="utf-8")


def default_output_path(root: Path, fmt: str) -> Path:
    suffix = "md" if fmt == "markdown" else "json"
    return root / "_report" / "manager" / f"coordination-dashboard-{iso_now()}.{suffix}"


def run_report(
    *,
    root: Path,
    fmt: str,
    manager_window: float,
    agent_window: float,
    directive_limit: int,
    output_path: Path | None,
    write_output_file: bool = True,
    compact: bool = False,
    stream=None,
) -> dict[str, Any]:
    data = build_dashboard(
        root,
        manager_window=manager_window,
        agent_window=agent_window,
        directive_limit=directive_limit,
    )
    if fmt == "json":
        content = json.dumps(data, indent=2, sort_keys=True)
    elif fmt == "markdown":
        content = render_markdown(data, compact=compact)
    else:
        raise DashboardError(f"Unsupported format '{fmt}'")

    if stream is None:
        print(content)
    else:
        if not content.endswith("\n"):
            content += "\n"
        stream.write(content)
        stream.flush()
    if write_output_file:
        output = output_path or default_output_path(root, fmt)
        write_output(content, output)
        try:
            location = output.relative_to(root)
        except ValueError:
            location = output
        if stream is None:
            print(f"Output written to {location}")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["report"], nargs="?", default="report")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--manager-window", type=float, default=DEFAULT_MANAGER_WINDOW_MINUTES)
    parser.add_argument("--agent-window", type=float, default=DEFAULT_AGENT_WINDOW_MINUTES)
    parser.add_argument("--messages", type=int, default=DEFAULT_DIRECTIVE_LIMIT, help="Number of manager directives to include")
    parser.add_argument("--output", type=Path, help="Optional output path (writes alongside stdout)")
    parser.add_argument(
        "--follow",
        type=float,
        default=0.0,
        help="Refresh interval in seconds; when >0, run in watch mode without writing files",
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Do not clear the terminal between follow iterations",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit a minimal agent-focused view",
    )
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    action = "report"
    alt_screen = False
    try:
        if args.follow and args.follow > 0:
            action = "follow"
            if not args.no_clear:
                sys.stdout.write("\033[?1049h")  # enter alternate screen buffer
                sys.stdout.flush()
                alt_screen = True
            while True:
                if args.no_clear:
                    sys.stdout.write("\033[H")
                else:
                    sys.stdout.write("\033[2J\033[H")
                sys.stdout.flush()
                run_report(
                    root=args.root,
                    fmt=args.format,
                    manager_window=args.manager_window,
                    agent_window=args.agent_window,
                    directive_limit=args.messages,
                    output_path=args.output,
                    write_output_file=False,
                    compact=args.compact,
                    stream=sys.stdout,
                )
                time.sleep(args.follow)
        else:
            run_report(
                root=args.root,
                fmt=args.format,
                manager_window=args.manager_window,
                agent_window=args.agent_window,
                directive_limit=args.messages,
                output_path=args.output,
                compact=args.compact,
                stream=None,
            )
    except KeyboardInterrupt:
        pass
    except DashboardError as exc:
        raise SystemExit(f"Dashboard error: {exc}") from exc
    finally:
        if alt_screen:
            sys.stdout.write("\033[?1049l")  # leave alternate screen
            sys.stdout.flush()

    record_usage(
        "agent.coord_dashboard",
        action=action,
        extra={
            "format": args.format,
            "manager_window": args.manager_window,
        "agent_window": args.agent_window,
        "messages": args.messages,
        "follow_interval": args.follow,
        "no_clear": bool(args.no_clear),
        "compact": bool(args.compact),
    },
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
