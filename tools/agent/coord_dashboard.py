#!/usr/bin/env python3
"""Generate a coordination dashboard aggregating plans, claims, and heartbeats."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from tools.usage.logger import record_usage

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
ROOT = Path(__file__).resolve().parents[2]
PLANS_DIRNAME = "_plans"
CLAIMS_DIRNAME = "_bus/claims"
EVENT_LOG = "_bus/events/events.jsonl"
MANAGER_MESSAGES = "_bus/messages/manager-report.jsonl"
ASSIGN_DIRNAME = "_bus/assignments"
DEFAULT_MANAGER_WINDOW_MINUTES = 30.0
DEFAULT_AGENT_WINDOW_MINUTES = 60.0
DEFAULT_DIRECTIVE_LIMIT = 10


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
        if plan.actor:
            agents.add(plan.actor)
    for claim in claims:
        if claim.agent_id:
            agents.add(claim.agent_id)
    for entry in events:
        agent = entry.get("agent_id")
        if isinstance(agent, str):
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
    for record in heartbeats.get("managers", []) + heartbeats.get("agents", []):
        if record.state != "active":
            message = f"Heartbeat {record.agent_id} is {record.state}"
            if message not in seen:
                alerts.append(message)
                seen.add(message)
    return alerts


def build_dashboard(
    root: Path,
    *,
    manager_window: float,
    agent_window: float,
    directive_limit: int,
) -> dict[str, Any]:
    plans = _collect_plan_summary(root)
    claims = _collect_claims(root)
    heartbeats = _collect_heartbeats(
        root,
        plans,
        claims,
        manager_window=manager_window,
        agent_window=agent_window,
    )
    directives = _collect_directives(root, directive_limit)
    alerts = _build_alerts(plans, heartbeats)
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


def render_markdown(data: dict[str, Any]) -> str:
    lines: list[str] = [f"# Coordination Dashboard — {data['generated_at']}", ""]

    plans = data.get("plans", [])
    lines.append("## Active Plans")
    if plans:
        table_rows = []
        for plan in plans:
            table_rows.append(
                (
                    plan.get("plan_id", "?"),
                    plan.get("actor", "-"),
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

    lines.append("## Heartbeats")
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
            lines.append(f"- {alert}")
    else:
        lines.append("- none")

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
        content = render_markdown(data)
    else:
        raise DashboardError(f"Unsupported format '{fmt}'")
    output = output_path or default_output_path(root, fmt)
    write_output(content, output)
    print(content)
    try:
        location = output.relative_to(root)
    except ValueError:
        location = output
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
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        run_report(
            root=args.root,
            fmt=args.format,
            manager_window=args.manager_window,
            agent_window=args.agent_window,
            directive_limit=args.messages,
            output_path=args.output,
        )
    except DashboardError as exc:
        raise SystemExit(f"Dashboard error: {exc}") from exc

    record_usage(
        "agent.coord_dashboard",
        action="report",
        extra={
            "format": args.format,
            "manager_window": args.manager_window,
            "agent_window": args.agent_window,
            "messages": args.messages,
        },
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
