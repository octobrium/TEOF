#!/usr/bin/env python3
"""Log BUS-COORD directives and mirror them to manager-report."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping, Optional, Sequence

from tools.agent import bus_message
from tools.usage.logger import record_usage

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POINTER_TASK = "manager-report"
DEFAULT_POINTER_TYPE = "status"


def _format_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _normalize_receipts(values: Iterable[str] | None) -> list[str]:
    return [value for value in (values or []) if value]


def _merge_meta(base: Mapping[str, object] | None, default_key: str, default_value: str) -> dict[str, object]:
    merged: dict[str, object] = dict(base or {})
    merged.setdefault(default_key, default_value)
    return merged


def log_directive_with_pointer(
    *,
    task_id: str,
    summary: str,
    directive_type: str,
    agent_id: Optional[str],
    branch: Optional[str],
    plan_id: Optional[str],
    receipts: Iterable[str] | None,
    meta: Mapping[str, object] | None,
    note: Optional[str],
    pointer_task: str,
    pointer_summary: str,
    pointer_type: str,
    pointer_plan_id: Optional[str],
    pointer_receipts: Iterable[str] | None,
    pointer_meta: Mapping[str, object] | None,
    pointer_note: Optional[str],
) -> tuple[Path, Path]:
    directive_path = bus_message.log_message(
        task_id=task_id,
        msg_type=directive_type,
        summary=summary,
        agent_id=agent_id,
        branch=branch,
        plan_id=plan_id,
        receipts=receipts,
        meta=meta,
        note=note,
    )

    merged_meta = _merge_meta(pointer_meta, "directive", task_id)
    pointer_path = bus_message.log_message(
        task_id=pointer_task,
        msg_type=pointer_type,
        summary=pointer_summary,
        agent_id=agent_id,
        branch=branch,
        plan_id=pointer_plan_id,
        receipts=pointer_receipts,
        meta=merged_meta,
        note=pointer_note,
    )

    record_usage(
        "directive_pointer",
        action="log",
        extra={
            "directive_task": task_id,
            "pointer_task": pointer_task,
            "pointer_type": pointer_type,
        },
    )

    return directive_path, pointer_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Log coordination directive and manager-report pointer")
    parser.add_argument("--task", required=True, help="Directive task id (e.g., BUS-COORD-0004)")
    parser.add_argument(
        "--summary",
        required=True,
        help="Summary for the directive entry",
    )
    parser.add_argument(
        "--type",
        default="directive",
        help="Directive message type (default: directive)",
    )
    parser.add_argument("--note", help="Optional note for the directive entry")
    parser.add_argument("--agent", help="Agent id (defaults to AGENT_MANIFEST.json)")
    parser.add_argument("--branch", help="Branch associated with the directive")
    parser.add_argument("--plan", help="Plan id to associate with both entries")
    parser.add_argument(
        "--receipt",
        action="append",
        help="Directive receipt (repeatable)",
    )
    parser.add_argument(
        "--meta",
        action="append",
        help="Directive metadata key=value (repeatable)",
    )

    parser.add_argument(
        "--pointer-task",
        default=DEFAULT_POINTER_TASK,
        help="Manager-report task id (default: manager-report)",
    )
    parser.add_argument(
        "--pointer-summary",
        help="Summary for the manager-report pointer (defaults to 'Directive <task> posted')",
    )
    parser.add_argument(
        "--pointer-note",
        help="Optional note for the manager-report pointer (defaults to 'See <task>')",
    )
    parser.add_argument(
        "--pointer-type",
        default=DEFAULT_POINTER_TYPE,
        help="Manager-report message type (default: status)",
    )
    parser.add_argument(
        "--pointer-plan",
        help="Plan id for the manager-report pointer (default: directive plan)",
    )
    parser.add_argument(
        "--pointer-receipt",
        action="append",
        help="Pointer receipt path (repeatable)",
    )
    parser.add_argument(
        "--pointer-meta",
        action="append",
        help="Pointer metadata key=value (repeatable)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    directive_meta: MutableMapping[str, object] = bus_message._parse_meta(args.meta)  # type: ignore[attr-defined]
    pointer_meta: MutableMapping[str, object] = bus_message._parse_meta(args.pointer_meta)  # type: ignore[attr-defined]

    pointer_summary = args.pointer_summary or f"Directive {args.task} posted"
    pointer_note = args.pointer_note or f"See {args.task}"
    pointer_plan = args.pointer_plan or args.plan

    directive_path, pointer_path = log_directive_with_pointer(
        task_id=args.task,
        summary=args.summary,
        directive_type=args.type,
        agent_id=args.agent,
        branch=args.branch,
        plan_id=args.plan,
        receipts=_normalize_receipts(args.receipt),
        meta=directive_meta,
        note=args.note,
        pointer_task=args.pointer_task,
        pointer_summary=pointer_summary,
        pointer_type=args.pointer_type,
        pointer_plan_id=pointer_plan,
        pointer_receipts=_normalize_receipts(args.pointer_receipt),
        pointer_meta=pointer_meta,
        pointer_note=pointer_note,
    )

    directive_display = _format_path(directive_path)
    pointer_display = _format_path(pointer_path)
    print(f"Logged directive to {directive_display} and pointer to {pointer_display}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
