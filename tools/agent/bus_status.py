#!/usr/bin/env python3
"""Summarize the agent coordination bus."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[2]
CLAIMS_DIR = ROOT / "_bus" / "claims"
EVENT_LOG = ROOT / "_bus" / "events" / "events.jsonl"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


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


def load_events(limit: int | None = None, *, since: datetime | None = None) -> list[dict[str, Any]]:
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
    *,
    agents: Sequence[str] | None,
    active_only: bool,
    since_filter: bool,
) -> None:
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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    claims = load_claims()
    since: datetime | None = None
    if args.since:
        try:
            since = datetime.strptime(args.since, ISO_FMT).replace(tzinfo=timezone.utc)
        except ValueError:
            parser.error("--since must be ISO8601 UTC (YYYY-MM-DDTHH:MM:SSZ)")
    events = load_events(limit=args.limit, since=since)
    agents = args.agent

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
            },
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    summarize(
        claims,
        events,
        agents=agents,
        active_only=args.active_only,
        since_filter=since is not None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
