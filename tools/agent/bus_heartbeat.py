#!/usr/bin/env python3
"""Monitor bus heartbeats and emit alerts/receipts."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
EVENT_LOG = ROOT / "_bus" / "events" / "events.jsonl"
MESSAGES_DIR = ROOT / "_bus" / "messages"
CLAIMS_DIR = ROOT / "_bus" / "claims"
ASSIGNMENTS_DIR = ROOT / "_bus" / "assignments"
MANIFEST_PATTERN = "AGENT_MANIFEST*.json"
PRIMARY_MANIFEST = ROOT / "AGENT_MANIFEST.json"

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
DEFAULT_MANAGER_WINDOW_MINUTES = 30.0
DEFAULT_AGENT_WINDOW_MINUTES = 240.0  # 4 hours
HEARTBEAT_EVENTS = {"handshake", "status"}
ACTIVE_CLAIM_STATUSES = {"active", "paused"}
ALERT_VERSION = 1
DEFAULT_MESSAGE_TASK = "manager-report"
DEFAULT_MESSAGE_TYPE = "status"


class HeartbeatError(RuntimeError):
    """Raised when CLI configuration or parsing fails."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso8601(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise HeartbeatError(
            "expected ISO8601 UTC timestamp (e.g. 2025-09-18T23:00:00Z)"
        ) from exc


def isoformat(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime(ISO_FMT)


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HeartbeatError(f"invalid JSON in {path}: {exc}") from exc


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for idx, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                raise HeartbeatError(f"invalid JSON on line {idx} of {path}") from None
            if isinstance(data, Mapping):
                entries.append(dict(data))
    return entries


def _parse_ts(raw: Any) -> datetime | None:
    if not isinstance(raw, str):
        return None
    try:
        return datetime.strptime(raw, ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def load_events(*, since: datetime | None) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for entry in _iter_jsonl(EVENT_LOG):
        ts = _parse_ts(entry.get("ts"))
        if since and (ts is None or ts < since):
            continue
        entry = dict(entry)
        entry.setdefault("_ts", ts)
        events.append(entry)
    return events


def load_messages_activity(*, since: datetime | None) -> dict[str, datetime]:
    activity: dict[str, datetime] = {}
    if not MESSAGES_DIR.exists():
        return activity
    for path in MESSAGES_DIR.glob("*.jsonl"):
        for entry in _iter_jsonl(path):
            agent_id = entry.get("from")
            ts = _parse_ts(entry.get("ts"))
            if not agent_id or ts is None:
                continue
            if since and ts < since:
                continue
            current = activity.get(agent_id)
            if current is None or ts > current:
                activity[agent_id] = ts
    return activity


def load_claims() -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    if not CLAIMS_DIR.exists():
        return claims
    for path in CLAIMS_DIR.glob("*.json"):
        try:
            data = _read_json(path)
        except HeartbeatError:
            continue
        if isinstance(data, Mapping):
            claims.append(dict(data))
    return claims


def _load_manifest_agent(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        data = _read_json(path)
    except HeartbeatError:
        return None
    agent_id = data.get("agent_id") if isinstance(data, Mapping) else None
    if isinstance(agent_id, str) and agent_id.strip():
        return agent_id.strip()
    return None


def load_manifest_agent() -> str | None:
    agent = _load_manifest_agent(PRIMARY_MANIFEST)
    if agent:
        return agent
    # fall back to first manifest variant
    variants = sorted(ROOT.glob(MANIFEST_PATTERN))
    for path in variants:
        agent = _load_manifest_agent(path)
        if agent:
            return agent
    return None


def _collect_manager_candidates() -> set[str]:
    candidates: set[str] = set()
    for path in ROOT.glob(MANIFEST_PATTERN):
        try:
            data = _read_json(path)
        except HeartbeatError:
            continue
        if not isinstance(data, Mapping):
            continue
        agent_id = str(data.get("agent_id", "")).strip()
        if not agent_id:
            continue
        desired_roles = data.get("desired_roles")
        if isinstance(desired_roles, Sequence) and any(role == "manager" for role in desired_roles):
            candidates.add(agent_id)
    if ASSIGNMENTS_DIR.exists():
        for path in ASSIGNMENTS_DIR.glob("*.json"):
            try:
                data = _read_json(path)
            except HeartbeatError:
                continue
            manager = data.get("manager") if isinstance(data, Mapping) else None
            if isinstance(manager, str) and manager.strip():
                candidates.add(manager.strip())
    return candidates


def summarize_manager_status(
    *,
    events: Sequence[Mapping[str, Any]],
    manager_ids: set[str],
    now: datetime,
    window_minutes: float,
) -> dict[str, Any]:
    window = window_minutes if window_minutes is not None else DEFAULT_MANAGER_WINDOW_MINUTES
    result = {
        "window_minutes": window,
        "candidates": sorted(manager_ids),
        "active": [],
        "stale": [],
        "missing": [],
    }
    if not manager_ids or window_minutes is None or window_minutes <= 0:
        return result

    threshold = timedelta(minutes=window_minutes)
    last_seen: dict[str, datetime] = {}
    for entry in events:
        agent_id = str(entry.get("agent_id", ""))
        if agent_id not in manager_ids:
            continue
        event_name = str(entry.get("event", ""))
        if event_name and event_name not in HEARTBEAT_EVENTS:
            continue
        ts = entry.get("_ts")
        if not isinstance(ts, datetime):
            ts = _parse_ts(entry.get("ts"))
        if ts is None:
            continue
        current = last_seen.get(agent_id)
        if current is None or ts > current:
            last_seen[agent_id] = ts

    for agent in sorted(manager_ids):
        ts = last_seen.get(agent)
        if ts is None:
            result["missing"].append({"agent_id": agent, "last_seen": None})
            continue
        if now - ts > threshold:
            result["stale"].append({"agent_id": agent, "last_seen": isoformat(ts)})
        else:
            result["active"].append({"agent_id": agent, "last_seen": isoformat(ts)})
    return result


def collect_last_activity(
    events: Sequence[Mapping[str, Any]],
    message_activity: Mapping[str, datetime],
) -> dict[str, datetime]:
    latest: dict[str, datetime] = {}
    for entry in events:
        agent_id = entry.get("agent_id")
        ts = entry.get("_ts")
        if not isinstance(agent_id, str) or not isinstance(ts, datetime):
            continue
        current = latest.get(agent_id)
        if current is None or ts > current:
            latest[agent_id] = ts
    for agent_id, ts in message_activity.items():
        current = latest.get(agent_id)
        if current is None or ts > current:
            latest[agent_id] = ts
    return latest


def summarize_agent_idle(
    *,
    claims: Sequence[Mapping[str, Any]],
    last_activity: Mapping[str, datetime],
    now: datetime,
    window_minutes: float,
) -> list[dict[str, Any]]:
    if window_minutes is None or window_minutes <= 0:
        return []
    threshold = timedelta(minutes=window_minutes)
    claims_by_agent: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for claim in claims:
        status = str(claim.get("status", "")).lower()
        if status not in ACTIVE_CLAIM_STATUSES:
            continue
        agent_id = str(claim.get("agent_id", "")).strip()
        if not agent_id:
            continue
        claims_by_agent[agent_id].append(claim)

    idle: list[dict[str, Any]] = []
    for agent_id, agent_claims in sorted(claims_by_agent.items()):
        last = last_activity.get(agent_id)
        last_str = isoformat(last) if isinstance(last, datetime) else None
        if last is not None and now - last <= threshold:
            continue
        entry_tasks = [str(c.get("task_id", "")) for c in agent_claims if c.get("task_id")]
        entry = {
            "agent_id": agent_id,
            "tasks": sorted(set(entry_tasks)),
            "last_activity": last_str,
            "window_minutes": window_minutes,
        }
        idle.append(entry)
    return idle


def build_alerts(
    manager_status: Mapping[str, Any],
    agent_idle: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    for entry in manager_status.get("missing", []) or []:
        alerts.append(
            {
                "type": "manager_heartbeat_missing",
                "agent_id": entry.get("agent_id"),
                "last_seen": entry.get("last_seen"),
            }
        )
    for entry in manager_status.get("stale", []) or []:
        alerts.append(
            {
                "type": "manager_heartbeat_stale",
                "agent_id": entry.get("agent_id"),
                "last_seen": entry.get("last_seen"),
            }
        )
    for entry in agent_idle:
        alerts.append(
            {
                "type": "agent_idle",
                "agent_id": entry.get("agent_id"),
                "tasks": entry.get("tasks", []),
                "last_activity": entry.get("last_activity"),
            }
        )
    return alerts


def compute_severity(alerts: Sequence[Mapping[str, Any]]) -> str:
    severity = "low"
    for alert in alerts:
        alert_type = alert.get("type")
        if alert_type in {"manager_heartbeat_missing", "manager_heartbeat_stale"}:
            return "high"
        if alert_type == "agent_idle":
            severity = "medium"
    return severity


def summarize_alerts(alerts: Sequence[Mapping[str, Any]]) -> str:
    if not alerts:
        return "Heartbeat status nominal"
    counter = Counter(alert.get("type", "unknown") for alert in alerts)
    parts = [f"{kind}={count}" for kind, count in sorted(counter.items())]
    return "Heartbeat alerts: " + ", ".join(parts)


def write_alert_receipt(
    payload: Mapping[str, Any],
    *,
    agent_id: str,
    alert_dir: Path | None,
) -> Path:
    if alert_dir is None:
        alert_dir = (
            ROOT
            / "_report"
            / "agent"
            / agent_id
            / "apoptosis-004"
            / "alerts"
        )
    alert_dir.mkdir(parents=True, exist_ok=True)
    ts_raw = str(payload.get("ts", ""))
    slug = ts_raw.replace(":", "").replace("-", "")
    filename = f"heartbeat-{slug or 'unknown'}.json"
    path = alert_dir / filename
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def relative_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def log_bus_event(
    *,
    agent_id: str,
    summary: str,
    receipts: Sequence[str],
    severity: str,
    task_id: str | None,
    plan_id: str | None,
    branch: str | None,
    alerts: Sequence[Mapping[str, Any]],
) -> None:
    payload: dict[str, Any] = {
        "ts": isoformat(utc_now()),
        "agent_id": agent_id,
        "event": "alert",
        "summary": summary,
        "severity": severity,
    }
    if task_id:
        payload["task_id"] = task_id
    if plan_id:
        payload["plan_id"] = plan_id
    if branch:
        payload["branch"] = branch
    if receipts:
        payload["receipts"] = list(receipts)
    if alerts:
        payload["alerts"] = list(alerts)

    EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with EVENT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def log_bus_message(
    *,
    task_id: str,
    summary: str,
    agent_id: str,
    receipts: Sequence[str],
    plan_id: str | None,
    message_type: str,
    note: str | None,
) -> None:
    from tools.agent import bus_message

    bus_message.log_message(
        task_id=task_id,
        msg_type=message_type,
        summary=summary,
        agent_id=agent_id,
        plan_id=plan_id,
        receipts=receipts,
        meta=None,
        note=note,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detect stale bus heartbeats and emit alerts")
    parser.add_argument(
        "--manager-window",
        type=float,
        default=DEFAULT_MANAGER_WINDOW_MINUTES,
        help="Minutes to expect a manager heartbeat (0 disables)",
    )
    parser.add_argument(
        "--agent-window",
        type=float,
        default=DEFAULT_AGENT_WINDOW_MINUTES,
        help="Minutes of inactivity before flagging agent idle (0 disables)",
    )
    parser.add_argument(
        "--now",
        help="Override current time (ISO8601 UTC); useful for tests",
    )
    parser.add_argument("--task", help="Task id for bus logging (optional)")
    parser.add_argument("--plan", help="Plan id for bus logging (optional)")
    parser.add_argument("--branch", help="Branch to associate with alerts (optional)")
    parser.add_argument("--agent-id", help="Agent id for receipts and logging (defaults to manifest)")
    parser.add_argument(
        "--alert-dir",
        help="Custom directory for alert receipts (defaults to _report/agent/<agent>/apoptosis-004/alerts)",
    )
    parser.add_argument(
        "--message-task",
        default=DEFAULT_MESSAGE_TASK,
        help="Bus message channel/task id (default: manager-report)",
    )
    parser.add_argument(
        "--message-type",
        default=DEFAULT_MESSAGE_TYPE,
        help="Bus message type when emitting alerts (default: status)",
    )
    parser.add_argument(
        "--note",
        help="Optional note to attach to the bus message",
    )
    parser.add_argument(
        "--ignore-manager",
        action="append",
        default=[],
        help="Manager id to exclude from heartbeat checks (repeatable)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip bus_event/bus_message writes; still records receipts",
    )
    parser.add_argument(
        "--no-bus-event",
        action="store_true",
        help="Disable emitting a bus_event entry",
    )
    parser.add_argument(
        "--no-bus-message",
        action="store_true",
        help="Disable emitting a bus_message entry",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        now = parse_iso8601(args.now) or utc_now()
    except HeartbeatError as exc:
        parser.error(str(exc))
        return 2

    agent_id = args.agent_id or load_manifest_agent()
    if not agent_id:
        parser.error("unable to determine agent id; use --agent-id or populate AGENT_MANIFEST")
        return 2

    alert_dir = Path(args.alert_dir) if args.alert_dir else None

    lookback_candidates = [
        args.manager_window if args.manager_window and args.manager_window > 0 else 0,
        args.agent_window if args.agent_window and args.agent_window > 0 else 0,
    ]
    lookback_minutes = max(lookback_candidates) if lookback_candidates else 0
    since = now - timedelta(minutes=lookback_minutes) if lookback_minutes > 0 else None

    try:
        events = load_events(since=since)
        message_activity = load_messages_activity(since=since)
        claims = load_claims()
        manager_ids = _collect_manager_candidates()
    except HeartbeatError as exc:
        parser.error(str(exc))
        return 2

    ignore_managers = {m.strip() for m in (args.ignore_manager or []) if m and m.strip()}
    if ignore_managers:
        manager_ids = {mid for mid in manager_ids if mid not in ignore_managers}

    manager_status = summarize_manager_status(
        events=events,
        manager_ids=manager_ids,
        now=now,
        window_minutes=args.manager_window,
    )
    last_activity = collect_last_activity(events, message_activity)
    agent_idle = summarize_agent_idle(
        claims=claims,
        last_activity=last_activity,
        now=now,
        window_minutes=args.agent_window,
    )
    alerts = build_alerts(manager_status, agent_idle)

    payload = {
        "version": ALERT_VERSION,
        "ts": isoformat(now),
        "manager": manager_status,
        "agent_idle": agent_idle,
        "alerts": alerts,
    }

    receipt_path = write_alert_receipt(payload, agent_id=agent_id, alert_dir=alert_dir)
    receipt_rel = relative_path(receipt_path)

    if alerts:
        severity = compute_severity(alerts)
        summary = summarize_alerts(alerts)
        receipts = [receipt_rel]
        if not args.dry_run and not args.no_bus_event:
            log_bus_event(
                agent_id=agent_id,
                summary=summary,
                receipts=receipts,
                severity=severity,
                task_id=args.task,
                plan_id=args.plan,
                branch=args.branch,
                alerts=alerts,
            )
        if not args.dry_run and not args.no_bus_message:
            task_id = args.message_task or DEFAULT_MESSAGE_TASK
            log_bus_message(
                task_id=task_id,
                summary=summary,
                agent_id=agent_id,
                receipts=receipts,
                plan_id=args.plan,
                message_type=args.message_type,
                note=args.note,
            )
        print(f"Alerts emitted; receipt at {receipt_rel}")
    else:
        print(f"Heartbeat OK; receipt at {receipt_rel}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
