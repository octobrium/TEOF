#!/usr/bin/env python3
"""Summarize claim + coordination history for a task."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
CLAIMS_DIR = ROOT / "_bus" / "claims"
EVENT_LOG = ROOT / "_bus" / "events" / "events.jsonl"
MESSAGES_DIR = ROOT / "_bus" / "messages"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.strptime(ts, ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def load_claim(task: str) -> dict | None:
    path = CLAIMS_DIR / f"{task}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise SystemExit(f"invalid JSON in {path}")


def summarize_claim(claim: dict | None, task: str) -> str:
    if not claim:
        return f"No claim found for {task}."
    parts = [
        f"Task: {task}",
        f"Agent: {claim.get('agent_id', '-')}",
        f"Status: {claim.get('status', '-')}",
    ]
    if claim.get("plan_id"):
        parts.append(f"Plan: {claim['plan_id']}")
    if claim.get("branch"):
        parts.append(f"Branch: {claim['branch']}")
    if claim.get("claimed_at"):
        parts.append(f"Claimed at: {claim['claimed_at']}")
    if claim.get("notes"):
        parts.append(f"Notes: {claim['notes']}")
    return " | ".join(parts)


def format_entries(entries: Iterable[dict], *, limit: int, title: str) -> str:
    selected = sorted(
        (entry for entry in entries if entry),
        key=lambda e: parse_iso(e.get("ts")) or datetime.min,
        reverse=True,
    )[:limit]
    if not selected:
        return f"{title}: none"
    lines = [f"{title} (latest {len(selected)}):"]
    for entry in selected:
        ts = entry.get("ts", "?")
        agent = entry.get("agent_id") or entry.get("from") or "?"
        kind = entry.get("event") or entry.get("type") or ""
        summary = entry.get("summary", "")
        plan = entry.get("plan_id")
        extra = f" plan={plan}" if plan else ""
        kind_part = f" [{kind}]" if kind else ""
        lines.append(f"  - {ts} :: {agent}{extra}{kind_part} :: {summary}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Show claim + bus history for a task")
    parser.add_argument("--task", required=True, help="Task identifier (e.g., QUEUE-010)")
    parser.add_argument("--limit", type=int, default=5, help="Max events/messages to display")
    args = parser.parse_args(argv)

    task = args.task.upper()
    claim = load_claim(task)
    print(summarize_claim(claim, task))

    events = [
        entry
        for entry in load_jsonl(EVENT_LOG)
        if entry.get("task_id") == task
    ]
    print(format_entries(events, limit=args.limit, title="Events"))

    msg_path = MESSAGES_DIR / f"{task}.jsonl"
    messages = load_jsonl(msg_path)
    print(format_entries(messages, limit=args.limit, title="Messages"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
