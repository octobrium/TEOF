#!/usr/bin/env python3
"""Summarise the plan backlog with status counts and prioritized pending items."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[2]
PLANS_DIR = ROOT / "_plans"
DEFAULT_LIMIT = 10
PENDING_STATUSES = {"queued", "in_progress"}


@dataclass
class PlanEntry:
    path: Path
    plan_id: str
    status: str
    priority: int | None
    layer: str | None
    systemic_scale: int | None
    created: datetime | None
    summary: str | None

    @property
    def relative_path(self) -> str:
        try:
            return self.path.relative_to(ROOT).as_posix()
        except ValueError:
            return self.path.as_posix()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_plans(directory: Path | None = None) -> Iterable[PlanEntry]:
    if directory is None:
        directory = PLANS_DIR
    if not directory.exists():
        return []
    for path in sorted(directory.glob("*.plan.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        plan_id = str(data.get("plan_id") or path.stem)
        status = str(data.get("status") or "unknown")
        priority = data.get("priority")
        if isinstance(priority, (int, float)):
            priority = int(priority)
        else:
            priority = None
        layer = data.get("layer") if isinstance(data.get("layer"), str) else None
        systemic = data.get("systemic_scale")
        if isinstance(systemic, (int, float)):
            systemic = int(systemic)
        else:
            systemic = None
        created = _parse_datetime(data.get("created") if isinstance(data.get("created"), str) else None)
        summary = data.get("summary") if isinstance(data.get("summary"), str) else None
        yield PlanEntry(
            path=path,
            plan_id=plan_id,
            status=status,
            priority=priority,
            layer=layer,
            systemic_scale=systemic,
            created=created,
            summary=summary,
        )


def summarise(entries: Iterable[PlanEntry]) -> dict[str, object]:
    entries = list(entries)
    status_counts: dict[str, int] = {}
    for entry in entries:
        status_counts[entry.status] = status_counts.get(entry.status, 0) + 1
    pending = [entry for entry in entries if entry.status in PENDING_STATUSES]
    pending.sort(key=lambda e: (e.priority if e.priority is not None else 999, e.created or datetime.max))
    return {
        "total": len(entries),
        "status_counts": status_counts,
        "pending": pending,
    }


def _format_pending(entries: Sequence[PlanEntry], limit: int) -> str:
    if not entries:
        return "No pending plans found."
    lines = ["Top pending plans (status priority layer systemic summary)"]
    for entry in entries[:limit]:
        pri = entry.priority if entry.priority is not None else "-"
        layer = entry.layer or "-"
        sys = entry.systemic_scale if entry.systemic_scale is not None else "-"
        summary = (entry.summary or "").strip()
        if len(summary) > 80:
            summary = summary[:77] + "..."
        lines.append(
            f"{entry.plan_id} [{entry.status}] p={pri} {layer} S={sys} :: {summary}\n  {entry.relative_path}"
        )
    if len(entries) > limit:
        lines.append(f"… {len(entries) - limit} more pending plans")
    return "\n".join(lines)


def format_summary(payload: dict[str, object], *, limit: int) -> str:
    status_counts = payload["status_counts"]
    status_lines = [f"  {status}: {count}" for status, count in sorted(status_counts.items())]
    pending_lines = _format_pending(payload["pending"], limit)
    return (
        f"Total plans: {payload['total']}\n"
        "Status counts:\n"
        + "\n".join(status_lines)
        + "\n\n"
        + pending_lines
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--status",
        action="append",
        help="Filter pending list by status (can repeat). Defaults to queued and in_progress.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Number of pending plans to display (default: {DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    status_filter = set(args.status) if args.status else PENDING_STATUSES
    entries = list(load_plans())
    summary = summarise(entries)
    if status_filter != PENDING_STATUSES:
        summary["pending"] = [entry for entry in summary["pending"] if entry.status in status_filter]

    if args.format == "json":
        payload = {
            "total": summary["total"],
            "status_counts": summary["status_counts"],
            "pending": [
                {
                    "plan_id": entry.plan_id,
                    "status": entry.status,
                    "priority": entry.priority,
                    "layer": entry.layer,
                    "systemic_scale": entry.systemic_scale,
                    "summary": entry.summary,
                    "path": entry.relative_path,
                }
                for entry in summary["pending"][: args.limit]
            ],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_summary(summary, limit=args.limit))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
