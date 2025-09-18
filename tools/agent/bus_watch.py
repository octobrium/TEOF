#!/usr/bin/env python3
"""Tail or filter agent bus events for real-time coordination."""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
EVENT_LOG = ROOT / "_bus" / "events" / "events.jsonl"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
DEFAULT_WINDOW_HOURS = 24.0


class BusWatchError(RuntimeError):
    """Raised when arguments or event parsing fail."""


def parse_iso8601(ts: str | None) -> datetime | None:
    if ts is None:
        return None
    try:
        return datetime.strptime(ts, ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise BusWatchError(
            "--since must be ISO8601 UTC (e.g. 2025-09-17T23:00:00Z)"
        ) from exc


def utc_now() -> datetime:
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc)


def compute_window_since(
    window_hours: float | None, *, now: datetime | None = None
) -> datetime | None:
    """Resolve the cutoff timestamp implied by the window size."""

    if window_hours is None:
        return None
    if window_hours < 0:
        raise BusWatchError("--window-hours must be >= 0")
    if window_hours == 0:
        return None
    reference = now or utc_now()
    return reference - timedelta(hours=window_hours)


def load_events(path: Path) -> list[Mapping[str, object]]:
    if not path.exists():
        return []
    events: list[Mapping[str, object]] = []
    with path.open("r", encoding="utf-8") as fh:
        for idx, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise BusWatchError(f"invalid JSON in events log (line {idx}): {exc}") from exc
    return events


def event_matches(
    event: Mapping[str, object],
    *,
    since: datetime | None,
    allowed_agents: Sequence[str] | None,
    allowed_events: Sequence[str] | None,
) -> bool:
    ts_raw = str(event.get("ts", ""))
    try:
        ts = datetime.strptime(ts_raw, ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError:
        return False

    if since and ts < since:
        return False

    if allowed_agents:
        agent_id = str(event.get("agent_id", ""))
        if agent_id not in allowed_agents:
            return False

    if allowed_events:
        event_name = str(event.get("event", ""))
        if event_name not in allowed_events:
            return False

    return True


def filter_events(
    events: Iterable[Mapping[str, object]],
    *,
    since: datetime | None,
    agents: Sequence[str] | None,
    events_filter: Sequence[str] | None,
) -> List[Mapping[str, object]]:
    selected: List[Mapping[str, object]] = []
    for event in events:
        if event_matches(
            event,
            since=since,
            allowed_agents=agents,
            allowed_events=events_filter,
        ):
            selected.append(event)
    return selected


def format_event(event: Mapping[str, object]) -> str:
    task = event.get("task_id", "-")
    summary = event.get("summary", "")
    receipts = event.get("receipts", [])
    receipt_suffix = ""
    if isinstance(receipts, list) and receipts:
        receipt_suffix = " :: receipts=" + ",".join(str(r) for r in receipts)
    return (
        f"{event.get('ts')} :: {event.get('agent_id')} :: {event.get('event')} :: "
        f"task={task} :: {summary}{receipt_suffix}"
    )


def stream_events(
    path: Path,
    *,
    since: datetime | None,
    agents: Sequence[str] | None,
    events_filter: Sequence[str] | None,
    follow: bool,
    limit: int | None,
) -> None:
    if not path.exists():
        print("bus-watch: event log missing; run session_boot or bus_event first")
        return

    try:
        with path.open("r", encoding="utf-8") as fh:
            lines = fh.readlines()
            events = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    print("bus-watch: skipping malformed event line", file=sys.stderr)
                    continue

            if limit is not None and limit > 0:
                events = events[-limit:]

            filtered = filter_events(
                events,
                since=since,
                agents=agents,
                events_filter=events_filter,
            )
            for event in filtered:
                print(format_event(event))

            if not follow:
                return

            while True:
                line = fh.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    print("bus-watch: skipping malformed event line", file=sys.stderr)
                    continue
                if event_matches(
                    event,
                    since=since,
                    allowed_agents=agents,
                    allowed_events=events_filter,
                ):
                    print(format_event(event))
    except KeyboardInterrupt:
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tail or filter agent bus events")
    parser.add_argument("--since", help="ISO8601 UTC timestamp (inclusive) to filter events")
    parser.add_argument("--agent", action="append", help="Filter by agent id (repeatable)")
    parser.add_argument("--event", dest="event_type", action="append", help="Filter by event name")
    parser.add_argument("--follow", action="store_true", help="Follow the log for new events")
    parser.add_argument("--limit", type=int, help="Restrict to the last N events before filtering")
    parser.add_argument(
        "--window-hours",
        type=float,
        default=DEFAULT_WINDOW_HOURS,
        help="Restrict to events within the most recent N hours (default: %(default)s; use 0 to disable)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        since = parse_iso8601(args.since)
    except BusWatchError as exc:
        parser.error(str(exc))
        return 2

    try:
        window_since = compute_window_since(args.window_hours)
    except BusWatchError as exc:
        parser.error(str(exc))
        return 2

    effective_since = None
    candidates = [cutoff for cutoff in (since, window_since) if cutoff is not None]
    if candidates:
        effective_since = max(candidates)

    try:
        stream_events(
            EVENT_LOG,
            since=effective_since,
            agents=args.agent,
            events_filter=args.event_type,
            follow=args.follow,
            limit=args.limit,
        )
    except BusWatchError as exc:
        parser.error(str(exc))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
