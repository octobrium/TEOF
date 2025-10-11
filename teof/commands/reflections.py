from __future__ import annotations

import datetime as dt
import json
import sys
from argparse import Namespace

from teof import reflections_report


def run(args: Namespace) -> int:
    reflections = reflections_report.collect_reflections(root=reflections_report.ROOT)

    if args.limit is not None and args.limit < 0:
        raise SystemExit("--limit must be non-negative")

    since = None
    if args.days is not None:
        if args.days < 0:
            raise SystemExit("--days must be non-negative")
        since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=args.days)

    filtered = reflections_report.filter_reflections(
        reflections,
        layers=getattr(args, "layers", None),
        tags=getattr(args, "tags", None),
        since=since,
    )

    summary = reflections_report.summarize(filtered)
    filters: dict[str, object] = {}
    if args.layers:
        filters["layers"] = args.layers
    if args.tags:
        filters["tags"] = args.tags
    if args.days is not None:
        filters["days"] = args.days

    if args.format == "json":
        payload = reflections_report.to_payload(
            filtered,
            limit=args.limit,
            summary=summary,
            filters=filters if filters else None,
        )
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    summary_text = reflections_report.format_summary(summary)
    if summary_text:
        print(summary_text)
        print()

    table = reflections_report.render_table(filtered, limit=args.limit)
    print(table)
    return 0


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    import argparse

    parser = subparsers.add_parser(
        "reflections",
        help="Summarise captured reflections and layer coverage",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional maximum number of reflections to include",
    )
    parser.add_argument(
        "--layer",
        action="append",
        dest="layers",
        help="Filter to reflections that include the specified layer (repeatable)",
    )
    parser.add_argument(
        "--tag",
        action="append",
        dest="tags",
        help="Filter to reflections that include the specified tag (repeatable)",
    )
    parser.add_argument(
        "--days",
        type=float,
        help="Show reflections captured within the last N days",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
