#!/usr/bin/env python3
"""Capture status and task snapshots for new contributors."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from teof import status_report, tasks_report

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"
DEFAULT_LIMIT = 15


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_agent() -> str | None:
    if not MANIFEST_PATH.exists():
        return None
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    agent_id = data.get("agent_id")
    if isinstance(agent_id, str) and agent_id.strip():
        return agent_id.strip()
    return None


def _relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", help="Agent id (defaults to AGENT_MANIFEST.json)")
    parser.add_argument(
        "--tasks-limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Number of tasks to include in the snapshot (default: %(default)s)",
    )
    parser.add_argument(
        "--include-done",
        action="store_true",
        help="Include completed tasks in the snapshot",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        help="Optional override for the onboarding receipt directory",
    )
    parser.add_argument(
        "--table",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Write a table view of the tasks in addition to JSON (default: enabled)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    agent_id = args.agent or _default_agent()
    if not agent_id:
        parser.error("Agent id missing; provide --agent or populate AGENT_MANIFEST.json")

    out_dir = args.out_dir or (ROOT / "_report" / "onboarding" / agent_id)
    timestamp = _iso_now()

    status_content = status_report.generate_status(ROOT)
    status_path = out_dir / f"status-{timestamp}.md"
    _write(status_path, status_content)

    records = tasks_report.collect_tasks(ROOT)
    records = tasks_report.filter_open_tasks(records, include_done=bool(args.include_done))
    records = tasks_report.sort_tasks(records)
    if args.tasks_limit is not None and args.tasks_limit >= 0:
        records = records[: args.tasks_limit]

    warnings = tasks_report.compute_warnings(records)

    tasks_json_path = out_dir / f"tasks-{timestamp}.json"
    tasks_payload = tasks_report.to_payload(records, warnings=warnings)
    _write(tasks_json_path, json.dumps(tasks_payload, ensure_ascii=False, indent=2) + "\n")

    table_path: Path | None = None
    if args.table:
        table_path = out_dir / f"tasks-{timestamp}.txt"
        table_content = tasks_report.render_table(records)
        if warnings:
            warning_lines = ["", "Warnings:"] + [f"- {item}" for item in warnings]
            table_content = "\n".join([table_content, *warning_lines])
        _write(table_path, table_content + "\n")

    summary_path = out_dir / f"onboarding-{timestamp}.json"
    summary_payload: dict[str, Any] = {
        "agent": agent_id,
        "generated_at": timestamp,
        "status_receipt": _relative(status_path),
        "tasks_receipt": _relative(tasks_json_path),
        "task_count": len(records),
        "warnings": warnings,
    }
    if table_path is not None:
        summary_payload["tasks_table"] = _relative(table_path)

    if records:
        summary_payload["tasks_preview"] = [asdict(record) for record in records[:3]]

    _write(summary_path, json.dumps(summary_payload, ensure_ascii=False, indent=2) + "\n")

    print("Onboarding check receipts:")
    print(f"- status: {_relative(status_path)}")
    print(f"- tasks: {_relative(tasks_json_path)}")
    if table_path is not None:
        print(f"- table: {_relative(table_path)}")
    print(f"- summary: {_relative(summary_path)}")
    if warnings:
        print("Warnings detected:")
        for item in warnings:
            print(f"- {item}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
