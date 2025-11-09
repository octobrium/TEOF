from __future__ import annotations

import json
import os
import sys
from argparse import Namespace

from teof import tasks_report


def run(args: Namespace) -> int:
    output_format = getattr(args, "format", "table")
    statuses = getattr(args, "statuses", None)
    priorities = getattr(args, "priorities", None)
    agents = getattr(args, "agents", None)
    plans = getattr(args, "plans", None)
    summary_only = bool(getattr(args, "summary", False))
    include_done = bool(getattr(args, "all", False))
    limit_value = getattr(args, "limit", None)
    limit = limit_value if isinstance(limit_value, int) and limit_value > 0 else None
    if statuses and any((status or "").strip().lower() == "done" for status in statuses):
        include_done = True

    root = tasks_report.ROOT
    records = tasks_report.collect_tasks(root=root)
    filtered = tasks_report.filter_open_tasks(
        records,
        include_done=include_done,
        statuses=statuses,
        priorities=priorities,
        agents=agents,
        plans=plans,
    )
    ordered = tasks_report.sort_tasks(filtered)
    warnings = tasks_report.compute_warnings(ordered)
    summary_data = tasks_report.summarize_tasks(ordered)
    total_filtered = len(ordered)
    if limit is not None and limit < total_filtered:
        display_tasks = ordered[:limit]
    else:
        display_tasks = ordered

    if output_format == "json":
        task_rows = [] if summary_only else display_tasks
        payload = tasks_report.to_payload(task_rows, warnings=warnings)
        payload["summary"] = summary_data
        payload["summary_only"] = summary_only
        payload["limit_applied"] = limit
        payload["total_filtered"] = total_filtered
        try:
            json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
        except BrokenPipeError:
            sys.stdout = open(os.devnull, "w")
            return 0
        return 0

    if summary_only:
        try:
            print("Summary:")
            print(f"- total: {summary_data['total']}")
            if summary_data["status"]:
                print("- by status:")
                for status, count in sorted(summary_data["status"].items()):
                    print(f"  - {status}: {count}")
            if summary_data["priority"]:
                print("- by priority:")
                for priority, count in sorted(summary_data["priority"].items()):
                    print(f"  - {priority}: {count}")
            print(f"- assignments: {summary_data['assignments']}")
            print(f"- claims: {summary_data['claims']}")
            print(f"- open without owner: {summary_data['open_unowned']}")
            print("\nWarnings:")
            if warnings:
                for warning in warnings:
                    print(f"- {warning}")
            else:
                print("- none")
        except BrokenPipeError:
            sys.stdout = open(os.devnull, "w")
            return 0
        return 0

    try:
        table = tasks_report.render_table(display_tasks)
        print(table)
        if limit is not None and limit < total_filtered:
            print(f"\nShowing {len(display_tasks)} of {total_filtered} tasks (limit={limit}).")
        print("\nWarnings:")
        if warnings:
            for warning in warnings:
                print(f"- {warning}")
        else:
            print("- none")
    except BrokenPipeError:
        sys.stdout = open(os.devnull, "w")
        return 0
    return 0


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    import argparse

    parser = subparsers.add_parser(
        "tasks",
        help="Summarise repository tasks (table or JSON)",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include completed tasks in the report",
    )
    parser.add_argument(
        "--status",
        dest="statuses",
        action="append",
        help="Filter by normalized status (repeat for multiple values)",
    )
    parser.add_argument(
        "--priority",
        dest="priorities",
        action="append",
        choices=("high", "medium", "low"),
        help="Filter by task priority (repeat for multiple values)",
    )
    parser.add_argument(
        "--agent",
        dest="agents",
        action="append",
        help="Filter by assignment or claim agent id (repeatable)",
    )
    parser.add_argument(
        "--plan",
        dest="plans",
        action="append",
        help="Filter by associated plan id (repeatable; matches task or claim plan)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show aggregate counts instead of the full table (JSON adds a summary block and omits tasks)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Show at most N tasks after filtering and sorting (default: no limit)",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
