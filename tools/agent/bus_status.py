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

PRESETS = {
    "support": {
        "limit": 20,
        "active_only": True,
        "window_hours": 6.0,
    },
    "manager": {
        "limit": 20,
        "active_only": False,
        "window_hours": 4.0,
        "manager_window": DEFAULT_MANAGER_WINDOW_MINUTES,
    },
}


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

    last_seen: dict[str, tuple[datetime, dict[str, Any]]] = {}
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
        prev = last_seen.get(agent_id)
        if prev is None or ts > prev[0]:
            last_seen[agent_id] = (ts, dict(entry))

    now = datetime.now(timezone.utc)
    threshold: timedelta | None = None
    if window_minutes is not None and window_minutes > 0:
        threshold = timedelta(minutes=window_minutes)

    excluded_meta_keys = {
        "agent_id",
        "event",
        "summary",
        "task_id",
        "plan_id",
        "branch",
        "ts",
        "_ts",
    }

    def _entry(agent: str, record: tuple[datetime, dict[str, Any]] | None) -> dict[str, Any]:
        ts = record[0] if record else None
        raw = record[1] if record else {}
        summary = raw.get("summary") if raw else None
        meta = {
            key: value
            for key, value in (raw or {}).items()
            if key not in excluded_meta_keys
        }
        return {
            "agent_id": agent,
            "last_seen": ts.strftime(ISO_FMT) if ts else None,
            "summary": summary,
            "meta": meta,
        }

    active: list[dict[str, Any]] = []
    stale: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []

    for agent in sorted(manager_ids):
        record = last_seen.get(agent)
        if record is None:
            missing.append(_entry(agent, None))
            continue
        ts = record[0]
        if threshold is not None and now - ts > threshold:
            stale.append(_entry(agent, record))
        else:
            active.append(_entry(agent, record))

    return {
        "window_minutes": window_minutes,
        "candidates": sorted(manager_ids),
        "active": active,
        "stale": stale,
        "missing": missing,
    }


def _format_manager_entry(entry: dict[str, Any]) -> str:
    agent = entry.get("agent_id")
    last_seen = entry.get("last_seen") or "unknown"
    parts = [f"{agent} (last {last_seen})"]
    summary = entry.get("summary")
    if summary:
        parts.append(summary)
    meta = entry.get("meta") or {}
    if meta:
        meta_str = ", ".join(f"{key}={value}" for key, value in sorted(meta.items()))
        if meta_str:
            parts.append(meta_str)
    return " :: ".join(parts)


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
                    print(f"  - {_format_manager_entry(entry)}")
            if stale_managers:
                print("  Stale:")
                for entry in stale_managers:
                    print(f"    - {_format_manager_entry(entry)}")
            if not active_managers:
                print("WARNING: No manager heartbeat within window.")
            if missing_managers:
                print("  Missing heartbeat:")
                for entry in missing_managers:
                    print(f"    - {_format_manager_entry(entry)}")
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


def _print_summary(
    claims: list[dict[str, Any]],
    events: list[dict[str, Any]],
    manager_status: dict[str, Any],
    *,
    agents: Sequence[str] | None,
    active_only: bool,
    since_filter: bool,
    preset: str | None,
    limit: int,
) -> None:
    filtered_claims = _filter_claims(claims, agents=agents, active_only=active_only)
    filtered_events = _filter_events(events, agents=agents)

    print("Summary")
    meta_parts = [f"limit={limit}"]
    if preset:
        meta_parts.append(f"preset={preset}")
    if since_filter:
        meta_parts.append("since-filter")
    meta_parts.append("active-only" if active_only else "all-claims")
    print(f"- settings: {', '.join(meta_parts)}")

    if filtered_claims:
        print(f"- claims ({len(filtered_claims)}):")
        for claim in filtered_claims:
            status = claim.get("status", "unknown")
            print(
                f"  * {claim.get('task_id')} [{status}] by {claim.get('agent_id')}"
                f" → {claim.get('branch')}"
            )
    else:
        print("- claims: none")

    if filtered_events:
        print(f"- events ({len(filtered_events)}):")
        for entry in filtered_events:
            print(
                f"  * {entry.get('ts')} :: {entry.get('agent_id')} :: {entry.get('event')}"
                f" :: {entry.get('summary', '')}"
            )
    else:
        print("- events: none")

    active = manager_status.get("active", [])
    stale = manager_status.get("stale", [])
    missing = manager_status.get("missing", [])
    if active:
        print("- manager heartbeat: active")
        for entry in active:
            print(f"  * {_format_manager_entry(entry)}")
    elif stale or missing:
        print("- manager heartbeat: stale")
        for entry in stale:
            print(f"  * stale {_format_manager_entry(entry)}")
        for entry in missing:
            print(f"  * missing {_format_manager_entry(entry)}")
    else:
        print("- manager heartbeat: none detected")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize the agent bus state")
    parser.add_argument(
        "--preset",
        choices=sorted(PRESETS.keys()),
        help="Apply a presets of recommended flags (support|manager)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Number of recent events to display (defaults to 10)",
    )
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
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a condensed bullet summary instead of verbose sections",
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
    preset_applied = None
    if args.preset:
        preset_applied = args.preset
        preset = PRESETS[args.preset]
        if args.limit is None and "limit" in preset:
            args.limit = preset["limit"]
        if not args.active_only and preset.get("active_only"):
            args.active_only = True
        if args.window_hours == DEFAULT_WINDOW_HOURS and "window_hours" in preset:
            args.window_hours = preset["window_hours"]
        if args.manager_window == DEFAULT_MANAGER_WINDOW_MINUTES and "manager_window" in preset:
            args.manager_window = preset["manager_window"]

    limit = args.limit if args.limit is not None else 10
    all_events = load_events(limit=None, since=since)
    events = all_events[-limit:] if limit else all_events
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
                "limit": limit,
                "since": args.since,
                "window_hours": args.window_hours,
                "manager_window": args.manager_window,
                "preset": preset_applied,
            },
            "manager_status": manager_status,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.summary:
        _print_summary(
            claims,
            events,
            manager_status,
            agents=agents,
            active_only=args.active_only,
            since_filter=since is not None,
            preset=preset_applied,
            limit=limit,
        )
    else:
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
