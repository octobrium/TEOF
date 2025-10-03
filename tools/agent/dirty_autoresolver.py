#!/usr/bin/env python3
"""Scan dirty handoff receipts and surface stale sessions."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from tools.agent import bus_message

ROOT = Path(__file__).resolve().parents[2]
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
DEFAULT_WARN_MINUTES = 30
DEFAULT_FAIL_MINUTES = 60
STATUS_OK = "ok"
STATUS_WARN = "warn"
STATUS_FAIL = "fail"
STATUS_ORDER = {STATUS_FAIL: 0, STATUS_WARN: 1, STATUS_OK: 2}


@dataclass
class ReceiptEntry:
    agent_id: str
    receipt_path: Path
    captured_at: datetime

    @property
    def age_minutes(self) -> float:
        delta = datetime.now(timezone.utc) - self.captured_at
        return delta.total_seconds() / 60.0


@dataclass
class AgentStatus:
    agent_id: str
    receipt: ReceiptEntry
    status: str


def _iso_now(now: datetime | None = None) -> str:
    if now is None:
        now = datetime.now(timezone.utc)
    return now.strftime(ISO_FMT)


def _parse_captured_at(lines: Iterable[str]) -> tuple[str | None, datetime | None]:
    agent_id: str | None = None
    captured_at: datetime | None = None
    for line in lines:
        line = line.strip()
        if not line.startswith("#"):
            continue
        if line.startswith("# agent="):
            agent_id = line.partition("=")[2].strip() or None
        elif line.startswith("# captured_at="):
            raw = line.partition("=")[2].strip()
            if raw:
                try:
                    captured_at = datetime.strptime(raw, ISO_FMT).replace(tzinfo=timezone.utc)
                except ValueError:
                    captured_at = None
    return agent_id, captured_at


def _load_receipt(path: Path) -> ReceiptEntry | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    agent_id, captured_at = _parse_captured_at(text.splitlines())
    if not captured_at:
        captured_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    if not agent_id:
        agent_id = path.parent.parent.name  # session/<agent>/dirty-handoff
    return ReceiptEntry(agent_id=agent_id, receipt_path=path, captured_at=captured_at)


def _session_root() -> Path:
    return ROOT / "_report" / "session"


def collect_receipts(now: datetime) -> list[AgentStatus]:
    session_root = _session_root()
    if not session_root.exists():
        return []
    per_agent: dict[str, ReceiptEntry] = {}
    for session_dir in session_root.iterdir():
        if not session_dir.is_dir():
            continue
        agent_id = session_dir.name
        dirty_dir = session_dir / "dirty-handoff"
        if not dirty_dir.exists():
            continue
        for path in sorted(dirty_dir.glob("dirty-*.txt")):
            receipt = _load_receipt(path)
            if receipt is None:
                continue
            # keep the newest captured_at
            current = per_agent.get(receipt.agent_id)
            if current is None or receipt.captured_at > current.captured_at:
                per_agent[receipt.agent_id] = receipt
    return [] if not per_agent else [AgentStatus(agent, entry, STATUS_OK) for agent, entry in per_agent.items()]


def classify(statuses: list[AgentStatus], warn_minutes: int, fail_minutes: int, now: datetime) -> None:
    for entry in statuses:
        age = (now - entry.receipt.captured_at).total_seconds() / 60.0
        if age >= fail_minutes:
            entry.status = STATUS_FAIL
        elif age >= warn_minutes:
            entry.status = STATUS_WARN
        else:
            entry.status = STATUS_OK


def render_table(statuses: list[AgentStatus], now: datetime) -> list[str]:
    if not statuses:
        return ["No dirty handoff receipts found."]
    headers = ["agent", "age(min)", "status", "receipt"]
    rows = []
    for entry in sorted(
        statuses,
        key=lambda item: (STATUS_ORDER.get(item.status, 3), -item.receipt.captured_at.timestamp()),
    ):
        age_minutes = (now - entry.receipt.captured_at).total_seconds() / 60.0
        rows.append(
            [
                entry.agent_id,
                f"{age_minutes:.1f}",
                entry.status,
                entry.receipt.receipt_path.relative_to(ROOT).as_posix(),
            ]
        )
    widths = [max(len(header), *(len(row[idx]) for row in rows)) for idx, header in enumerate(headers)]
    lines = [" | ".join(header.ljust(widths[idx]) for idx, header in enumerate(headers)),
             " | ".join("-" * widths[idx] for idx in range(len(headers)))]
    for row in rows:
        lines.append(" | ".join(row[idx].ljust(widths[idx]) for idx in range(len(headers))))
    return lines


def build_summary(statuses: list[AgentStatus], warn_minutes: int, fail_minutes: int, now: datetime) -> dict[str, Any]:
    payload = {
        "generated_at": _iso_now(now),
        "warn_threshold_minutes": warn_minutes,
        "fail_threshold_minutes": fail_minutes,
        "agents": [],
    }
    for entry in sorted(statuses, key=lambda item: item.agent_id):
        payload["agents"].append(
            {
                "agent_id": entry.agent_id,
                "latest_receipt": entry.receipt.receipt_path.relative_to(ROOT).as_posix(),
                "captured_at": entry.receipt.captured_at.strftime(ISO_FMT),
                "age_minutes": round((now - entry.receipt.captured_at).total_seconds() / 60.0, 2),
                "status": entry.status,
            }
        )
    return payload


def _bus_summary(statuses: list[AgentStatus]) -> str:
    if not statuses:
        return "Dirty handoff resolver: 0 receipts"
    parts = []
    for entry in sorted(statuses, key=lambda item: item.agent_id):
        parts.append(f"{entry.agent_id}={entry.status}")
    return "Dirty handoff resolver: " + ", ".join(parts)


def resolve_exit_code(statuses: list[AgentStatus]) -> int:
    any_fail = any(entry.status == STATUS_FAIL for entry in statuses)
    any_warn = any(entry.status == STATUS_WARN for entry in statuses)
    if any_fail:
        return 2
    if any_warn:
        return 1
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve dirty handoff receipts")
    parser.add_argument("--warn-age-minutes", type=int, default=DEFAULT_WARN_MINUTES)
    parser.add_argument("--max-age-minutes", type=int, default=DEFAULT_FAIL_MINUTES)
    parser.add_argument("--output", type=Path, help="Optional JSON summary output path")
    parser.add_argument("--bus-message", action="store_true", help="Send summary to manager-report")
    parser.add_argument("--dry-run", action="store_true", help="Only print summary, skip writes/messages")
    parser.add_argument("--now", help="Override current time (ISO 8601, UTC)")
    parser.add_argument("--plan", help="Plan identifier for bus message metadata")
    parser.add_argument("--task", help="Task identifier for bus message metadata")
    return parser.parse_args(argv)


def _parse_now(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.strptime(value, ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise SystemExit(f"Invalid --now value {value!r}; expected ISO format {ISO_FMT}") from exc


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    now = _parse_now(args.now)
    statuses = collect_receipts(now)
    classify(statuses, warn_minutes=args.warn_age_minutes, fail_minutes=args.max_age_minutes, now=now)

    for line in render_table(statuses, now):
        print(line)

    summary = build_summary(statuses, args.warn_age_minutes, args.max_age_minutes, now)
    output_path: Path | None = None
    if args.output:
        output_path = args.output
        if not output_path.is_absolute():
            output_path = (ROOT / output_path).resolve()

    if output_path and not args.dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        try:
            display_path = output_path.relative_to(ROOT)
        except ValueError:
            display_path = output_path
        print(f"Summary written to {display_path}")

    if args.bus_message and not args.dry_run:
        message = _bus_summary(statuses)
        receipts = []
        if output_path:
            try:
                receipt_rel = output_path.relative_to(ROOT).as_posix()
            except ValueError:
                receipt_rel = output_path.as_posix()
            receipts.append(receipt_rel)
        bus_message.log_message(
            task_id=args.task or "manager-report",
            msg_type="status",
            summary=message,
            agent_id=None,
            plan_id=args.plan,
            receipts=receipts,
        )

    return resolve_exit_code(statuses)


if __name__ == "__main__":
    raise SystemExit(main())
