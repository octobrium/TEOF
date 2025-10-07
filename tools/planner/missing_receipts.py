#!/usr/bin/env python3
"""List plan files missing top-level receipts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
PLANS_DIR = ROOT / "_plans"
DEFAULT_STATUSES = {"queued", "in_progress"}


def load_plans(directory: Path) -> Iterable[Path]:
    if not directory.exists():
        return []
    yield from sorted(directory.glob("*.plan.json"))


def plan_has_receipts(data: dict[str, object]) -> bool:
    receipts = data.get("receipts")
    return isinstance(receipts, list) and bool(receipts)


def load_missing(status_filter: set[str]) -> list[dict[str, object]]:
    missing: list[dict[str, object]] = []
    for path in load_plans(PLANS_DIR):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        status = str(data.get("status") or "unknown")
        if status_filter and status not in status_filter:
            continue
        if plan_has_receipts(data):
            continue
        summary = data.get("summary") if isinstance(data.get("summary"), str) else ""
        try:
            rel_path = path.relative_to(ROOT).as_posix()
        except ValueError:
            rel_path = path.as_posix()
        missing.append(
            {
                "plan_id": str(data.get("plan_id") or path.stem),
                "status": status,
                "path": rel_path,
                "summary": summary,
            }
        )
    return missing


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--status",
        action="append",
        help="Restrict to specific statuses (default: queued, in_progress)",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    return parser


def format_table(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "All matching plans contain receipts."
    lines = ["Plans missing top-level receipts:"]
    for row in rows:
        summary = (row["summary"] or "").strip()
        if len(summary) > 80:
            summary = summary[:77] + "..."
        lines.append(f"{row['plan_id']} [{row['status']}] :: {summary}\n  {row['path']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    statuses = set(args.status) if args.status else DEFAULT_STATUSES
    rows = load_missing(statuses)
    if args.format == "json":
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        print(format_table(rows))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
