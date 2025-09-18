#!/usr/bin/env python3
"""Summarize the agent coordination bus."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[2]
CLAIMS_DIR = ROOT / "_bus" / "claims"
EVENT_LOG = ROOT / "_bus" / "events" / "events.jsonl"
ASSIGNMENTS_DIR = ROOT / "_bus" / "assignments"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
MANIFEST_PATTERN = "AGENT_MANIFEST*.json"
HEARTBEAT_EVENTS = {"handshake", "status"}
DEFAULT_MANAGER_WINDOW_MINUTES = 30.0
DEFAULT_WINDOW_HOURS = 24.0


def load_claims() -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    if not CLAIMS_DIR.exists():
        return claims
    for path in sorted(CLAIMS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
        data["_path"] = path.relative_to(ROOT).as_posix()
        claims.append(data)
    return claims


def _parse_ts(raw: str) -> datetime | None:
    try:
        return datetime.strptime(raw, ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def load_events(
    limit: int | None = None,
    *,
    since: datetime | None = None,
) -> list[dict[str, Any]]:
    if not EVENT_LOG.exists():
        return []
    events: list[dict[str, Any]] = []
    with EVENT_LOG.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON in events log: {exc}") from exc
    if since is not None:
        filtered: list[dict[str, Any]] = []
        for entry in events:
            ts_raw = str(entry.get("ts", ""))
            ts = _parse_ts(ts_raw)
            if ts is None or ts < since:
                continue
            filtered.append(entry)
        events = filtered
    if limit is not None:
        events = events[-limit:]
    for idx, entry in enumerate(events):
        entry["_index"] = len(events) - idx
    return events


ACTIVE_STATUSES = {"active", "paused"}


def _load_manifests() -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    for path in ROOT.glob(MANIFEST_PATTERN):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON in manifest {path}: {exc}") from exc
        data["_path"] = path.relative_to(ROOT).as_posix()
        manifests.append(data)
    return manifests


def _load_assignment_managers() -> set[str]:
    managers: set[str] = set()
    if not ASSIGNMENTS_DIR.exists():
        return managers
    for path in ASSIGNMENTS_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON in assignment {path}: {exc}") from exc
        manager = data.get("manager")
        if isinstance(manager, str) and manager.strip():
            managers.add(manager.strip())
    return managers


def _collect_manager_candidates(manifests: list[dict[str, Any]]) -> set[str]:
    candidates: set[str] = set()
    for manifest in manifests:
        desired_roles = manifest.get("desired_roles") or []
        if not isinstance(desired_roles, list):
            continue
        agent_id = str(manifest.get("agent_id", "")).strip()
        if not agent_id:
            continue
        if any(role == "manager" for role in desired_roles):
            candidates.add(agent_id)
    candidates.update(_load_assignment_managers())
    return candidates


def _detect_manager_status(
    manager_ids: set[str],
    events: Sequence[dict[str, Any]],
    *,
    window_minutes: float | None,
) -> dict[str, Any]:
    if not manager_ids:
        return {
            "window_minutes": window_minutes,
            "candidates": [],
            "active": [],
            "stale": [],
            "missing": [],
        }

    last_seen: dict[str, datetime] = {}
    for entry in events:
        agent_id = str(entry.get("agent_id", ""))
        if agent_id not in manager_ids:
            continue
        event_type = str(entry.get("event", ""))
        if event_type and event_type not in HEARTBEAT_EVENTS:
            continue
        ts = _parse_ts(str(entry.get("ts", "")))
        if ts is None:
            continue
        last_seen[agent_id] = ts

    now = datetime.now(timezone.utc)
    threshold: timedelta | None = None
    if window_minutes is not None and window_minutes > 0:
        threshold = timedelta(minutes=window_minutes)

    def _entry(agent: str, ts: datetime | None) -> dict[str, Any]:
        return {
            "agent_id": agent,
            "last_seen": ts.strftime(ISO_FMT) if ts else None,
        }

    active: list[dict[str, Any]] = []
    stale: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []

    for agent in sorted(manager_ids):
        ts = last_seen.get(agent)
        if ts is None:
            missing.append(_entry(agent, None))
            continue
        if threshold is not None and now - ts > threshold:
            stale.append(_entry(agent, ts))
        else:
            active.append(_entry(agent, ts))

    return {
        "window_minutes": window_minutes,
        "candidates": sorted(manager_ids),
        "active": active,
        "stale": stale,
        "missing": missing,
    }


def _filter_claims(
    claims: Iterable[dict[str, Any]],
    *,
    agents: Sequence[str] | None,
    active_only: bool,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for claim in claims:
        agent_id = str(claim.get("agent_id", ""))
        if agents and agent_id not in agents:
            continue
        if active_only and claim.get("status") not in ACTIVE_STATUSES:
            continue
        selected.append(claim)
    return selected


def _filter_events(
    events: Iterable[dict[str, Any]],
    *,
    agents: Sequence[str] | None,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for event in events:
        agent_id = str(event.get("agent_id", ""))
        if agents and agent_id not in agents:
            continue
        selected.append(event)
    return selected


def summarize(
    claims: list[dict[str, Any]],
    events: list[dict[str, Any]],
    manager_status: dict[str, Any],
    *,
    agents: Sequence[str] | None,
    active_only: bool,
    since_filter: bool,
) -> None:
    window = manager_status.get("window_minutes")
    candidates = manager_status.get("candidates", [])
    active_managers = manager_status.get("active", [])
    stale_managers = manager_status.get("stale", [])
    missing_managers = manager_status.get("missing", [])

    if window is not None and window <= 0:
        print("Manager heartbeat check disabled (--manager-window 0).\n")
    else:
        if not candidates:
            print("No manager candidates discovered.\n")
        else:
            window_str = f"{window:.0f}m" if window else "n/a"
            print(f"Managers (window {window_str}):")
            if active_managers:
                for entry in active_managers:
                    print(f"  - {entry['agent_id']} (last {entry['last_seen']})")
            if stale_managers:
                print("  Stale:")
                for entry in stale_managers:
                    print(f"    - {entry['agent_id']} (last {entry['last_seen']})")
            if not active_managers:
                print("WARNING: No manager heartbeat within window.")
            if missing_managers:
                print("  Missing heartbeat:")
                for entry in missing_managers:
                    print(f"    - {entry['agent_id']}")
            print()

    claim_filters = bool(agents) or active_only
    event_filters = bool(agents) or since_filter
    filtered_claims = _filter_claims(claims, agents=agents, active_only=active_only)
    filtered_events = _filter_events(events, agents=agents)

    if filtered_claims:
        print("Active claims:")
        for claim in filtered_claims:
            status = claim.get("status", "unknown")
            print(
                f"  - {claim.get('task_id')} [{status}] by {claim.get('agent_id')}"
                f" → {claim.get('branch')} (plan={claim.get('plan_id', 'N/A')})"
            )
    else:
        msg = "No claims matching filters." if claim_filters else "No claims recorded."
        print(msg)

    if filtered_events:
        print("\nRecent events:")
        for entry in filtered_events:
            task = entry.get("task_id", "-")
            summary = entry.get("summary", "")
            print(
                f"  - {entry.get('ts')} :: {entry.get('agent_id')} :: {entry.get('event')}"
                f" :: task={task} :: {summary}"
            )
    else:
        msg = "No events matching filters." if event_filters else "No events recorded."
        print(f"\n{msg}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize the agent bus state")
    parser.add_argument("--limit", type=int, default=10, help="Number of recent events to display")
    parser.add_argument(
        "--agent",
        action="append",
        help="Filter claims and events by agent id (repeatable)",
    )
    parser.add_argument(
        "--active-only",
        action="store_true",
        help="Show only active or paused claims",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON summary instead of plain text",
    )
    parser.add_argument(
        "--since",
        help="Filter events at or after the ISO8601 UTC timestamp (e.g. 2025-09-18T00:00:00Z)",
    )
    parser.add_argument(
        "--window-hours",
        type=float,
        default=DEFAULT_WINDOW_HOURS,
        help=(
            "Restrict events to the most recent N hours (default: %(default).0f). "
            "Use 0 to disable the window."
        ),
    )
    parser.add_argument(
        "--manager-window",
        type=float,
        default=DEFAULT_MANAGER_WINDOW_MINUTES,
        help="Minutes to look back for manager heartbeat (0 disables the check)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    claims = load_claims()
    if args.window_hours is not None and args.window_hours < 0:
        parser.error("--window-hours must be greater than or equal to 0")
    since: datetime | None = None
    if args.since:
        try:
            since = datetime.strptime(args.since, ISO_FMT).replace(tzinfo=timezone.utc)
        except ValueError:
            parser.error("--since must be ISO8601 UTC (YYYY-MM-DDTHH:MM:SSZ)")
    elif args.window_hours:
        since = datetime.now(timezone.utc) - timedelta(hours=args.window_hours)
    all_events = load_events(limit=None, since=since)
    events = all_events[-args.limit :] if args.limit else all_events
    agents = args.agent

    manifests = _load_manifests()
    manager_candidates = _collect_manager_candidates(manifests)
    manager_status = _detect_manager_status(
        manager_candidates,
        all_events,
        window_minutes=args.manager_window,
    )

    if args.json:
        filtered_claims = _filter_claims(claims, agents=agents, active_only=args.active_only)
        filtered_events = _filter_events(events, agents=agents)
        payload = {
            "claims": filtered_claims,
            "events": filtered_events,
            "filters": {
                "agents": agents or [],
                "active_only": args.active_only,
                "limit": args.limit,
                "since": args.since,
                "window_hours": args.window_hours,
                "manager_window": args.manager_window,
            },
            "manager_status": manager_status,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    summarize(
        claims,
        events,
        manager_status,
        agents=agents,
        active_only=args.active_only,
        since_filter=since is not None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
