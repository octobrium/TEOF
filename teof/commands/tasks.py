from __future__ import annotations

import json
import sys
from argparse import Namespace

from teof import tasks_report


def run(args: Namespace) -> int:
    include_done = bool(getattr(args, "all", False))
    output_format = getattr(args, "format", "table")

    root = tasks_report.ROOT
    records = tasks_report.collect_tasks(root=root)
    filtered = tasks_report.filter_open_tasks(records, include_done=include_done)
    ordered = tasks_report.sort_tasks(filtered)
    warnings = tasks_report.compute_warnings(ordered)

    if output_format == "json":
        payload = tasks_report.to_payload(ordered, warnings=warnings)
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    table = tasks_report.render_table(ordered)
    print(table)
    print("\nWarnings:")
    if warnings:
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("- none")
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
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
