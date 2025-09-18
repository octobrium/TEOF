#!/usr/bin/env python3
"""Summarize tool usage logs."""
from __future__ import annotations

import argparse
import collections
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
USAGE_LOG = ROOT / "_report" / "usage" / "tools.jsonl"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _parse_ts(raw: str) -> datetime | None:
    try:
        return datetime.strptime(raw, ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def load_entries() -> list[dict]:
    if not USAGE_LOG.exists():
        return []
    entries: list[dict] = []
    with USAGE_LOG.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def filter_entries(entries: list[dict], *, cutoff: datetime | None) -> list[dict]:
    if cutoff is None:
        return entries
    filtered: list[dict] = []
    for entry in entries:
        ts_raw = entry.get("ts")
        if isinstance(ts_raw, str):
            ts = _parse_ts(ts_raw)
            if ts and ts >= cutoff:
                filtered.append(entry)
    return filtered


def summarize(entries: list[dict]) -> tuple[dict[str, int], dict[str, list[dict]]]:
    counts: dict[str, int] = collections.Counter()
    latest: dict[str, list[dict]] = collections.defaultdict(list)
    for entry in entries:
        tool = str(entry.get("tool", "unknown"))
        counts[tool] += 1
        latest[tool].append(entry)
    for tool, logs in latest.items():
        logs.sort(key=lambda e: e.get("ts", ""), reverse=True)
    return counts, latest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize tool usage logs")
    parser.add_argument("--hours", type=float, help="Show entries within the last N hours")
    parser.add_argument("--limit", type=int, default=3, help="How many recent entries per tool to display")
    args = parser.parse_args(argv)

    cutoff = None
    if args.hours:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=args.hours)

    entries = filter_entries(load_entries(), cutoff=cutoff)
    counts, latest = summarize(entries)

    if not counts:
        print("No usage data recorded yet.")
        return 0

    print("Tool usage counts:")
    for tool, count in sorted(counts.items(), key=lambda item: item[1], reverse=True):
        print(f"- {tool}: {count}")
        for entry in latest[tool][: args.limit]:
            extra = {k: v for k, v in entry.items() if k not in {"tool", "action", "ts"}}
            suffix = f" {extra}" if extra else ""
            print(f"    {entry.get('ts', '?')} :: {entry.get('action', 'run')}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
