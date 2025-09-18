#!/usr/bin/env python3
"""Summarize consensus-related state for managers and reviewers."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
ROOT = Path(__file__).resolve().parents[2]
EVENT_LOG = ROOT / "_bus" / "events" / "events.jsonl"
MANAGER_REPORT = ROOT / "_bus" / "messages" / "manager-report.jsonl"
ASSIGNMENTS_DIR = ROOT / "_bus" / "assignments"
DEFAULT_TASKS = ("QUEUE-030", "QUEUE-031", "QUEUE-032", "QUEUE-033")


@dataclass
class ItemSummary:
    task_id: str
    manager: str | None
    status: str
    last_update: str | None
    plan_id: str | None
    receipts: list[str]
    message_count: int
    event_count: int


def _parse_ts(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _load_jsonl(path: Path) -> list[dict]:
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
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    return entries


def _load_assignment_manager(task_id: str) -> str | None:
    if not ASSIGNMENTS_DIR.exists():
        return None
    path = ASSIGNMENTS_DIR / f"{task_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in assignment {path}: {exc}") from exc
    manager = data.get("manager")
    if isinstance(manager, str) and manager.strip():
        return manager.strip()
    return None


def _collect_summaries(
    *,
    tasks: Sequence[str],
    since: datetime | None,
) -> list[ItemSummary]:
    events = _load_jsonl(EVENT_LOG)
    messages = _load_jsonl(MANAGER_REPORT)

    by_task_events: dict[str, list[dict]] = defaultdict(list)
    for entry in events:
        task_id = str(entry.get("task_id", ""))
        if task_id not in tasks:
            continue
        ts = _parse_ts(entry.get("ts"))
        if since and (ts is None or ts < since):
            continue
        entry["_ts"] = ts
        by_task_events[task_id].append(entry)

    by_task_messages: dict[str, list[dict]] = defaultdict(list)
    for entry in messages:
        task_id = str(entry.get("task_id", ""))
        if task_id not in tasks:
            continue
        ts = _parse_ts(entry.get("ts"))
        if since and (ts is None or ts < since):
            continue
        entry["_ts"] = ts
        by_task_messages[task_id].append(entry)

    summaries: list[ItemSummary] = []
    for task in tasks:
        events_for_task = by_task_events.get(task, [])
        messages_for_task = by_task_messages.get(task, [])
        last_event = max(events_for_task, key=lambda e: e.get("_ts") or datetime.min, default=None)
        receipts: list[str] = []
        plan_id = None
        status = "unknown"
        last_update = None
        if last_event:
            status = str(last_event.get("event", "unknown"))
            plan_id = last_event.get("plan_id")
            last_ts = last_event.get("_ts")
            if last_ts:
                last_update = last_ts.strftime(ISO_FMT)
            recs = last_event.get("receipts")
            if isinstance(recs, list):
                receipts.extend(str(r) for r in recs)
            receipt = last_event.get("receipt")
            if isinstance(receipt, str):
                receipts.append(receipt)
        manager = _load_assignment_manager(task)
        summaries.append(
            ItemSummary(
                task_id=task,
                manager=manager,
                status=status,
                last_update=last_update,
                plan_id=plan_id,
                receipts=sorted(set(receipts)),
                message_count=len(messages_for_task),
                event_count=len(events_for_task),
            )
        )
    return summaries


def _format_table(items: Iterable[ItemSummary]) -> str:
    rows = [
        [
            "Task",
            "Manager",
            "Status",
            "Last Update",
            "Plan",
            "Receipts",
            "Events",
            "Messages",
        ]
    ]
    for item in items:
        rows.append(
            [
                item.task_id,
                item.manager or "-",
                item.status,
                item.last_update or "-",
                item.plan_id or "-",
                ", ".join(item.receipts) if item.receipts else "-",
                str(item.event_count),
                str(item.message_count),
            ]
        )

    widths = [max(len(row[col]) for row in rows) for col in range(len(rows[0]))]
    lines: list[str] = []
    for idx, row in enumerate(rows):
        line = " | ".join(cell.ljust(widths[col]) for col, cell in enumerate(row))
        lines.append(line)
        if idx == 0:
            lines.append("-+-".join("-" * width for width in widths))
    return "\n".join(lines)


def _format_markdown(items: Iterable[ItemSummary]) -> str:
    header = "| Task | Manager | Status | Last Update | Plan | Receipts | Events | Messages |"
    divider = "| --- | --- | --- | --- | --- | --- | --- | --- |"
    rows = [header, divider]
    for item in items:
        rows.append(
            "| {task} | {manager} | {status} | {last_update} | {plan} | {receipts} | {events} | {messages} |".format(
                task=item.task_id,
                manager=item.manager or "-",
                status=item.status,
                last_update=item.last_update or "-",
                plan=item.plan_id or "-",
                receipts=", ".join(item.receipts) if item.receipts else "-",
                events=item.event_count,
                messages=item.message_count,
            )
        )
    return "\n".join(rows)


def _format_json(items: Iterable[ItemSummary]) -> str:
    return json.dumps([
        {
            "task_id": item.task_id,
            "manager": item.manager,
            "status": item.status,
            "last_update": item.last_update,
            "plan_id": item.plan_id,
            "receipts": item.receipts,
            "event_count": item.event_count,
            "message_count": item.message_count,
        }
        for item in items
    ], ensure_ascii=False, indent=2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize consensus decisions")
    parser.add_argument(
        "--task",
        action="append",
        help="Specific task id to include (repeatable); defaults to consensus backlog tasks",
    )
    parser.add_argument(
        "--since",
        help="Only include events/messages after this ISO8601 UTC timestamp",
    )
    parser.add_argument(
        "--format",
        choices=["table", "markdown", "json"],
        default="table",
        help="Output format",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    tasks = tuple(args.task) if args.task else DEFAULT_TASKS
    since: datetime | None = None
    if args.since:
        try:
            since = datetime.strptime(args.since, ISO_FMT).replace(tzinfo=timezone.utc)
        except ValueError:
            parser.error("--since must be ISO8601 UTC (YYYY-MM-DDTHH:MM:SSZ)")

    summaries = _collect_summaries(tasks=tasks, since=since)

    if args.format == "json":
        print(_format_json(summaries))
    elif args.format == "markdown":
        print(_format_markdown(summaries))
    else:
        print(_format_table(summaries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
