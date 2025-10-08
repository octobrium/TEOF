from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from tools.autonomy import frontier as frontier_mod

from ._utils import module_root, relpath


def run(args: Namespace) -> int:
    base_root = module_root(frontier_mod)
    out_path = None
    if args.out is not None:
        out_path = args.out if args.out.is_absolute() else base_root / args.out
    result = frontier_mod.compute_frontier(limit=max(0, args.limit))
    if args.format == "json":
        print(json.dumps([entry.as_dict() for entry in result], ensure_ascii=False, indent=2))
    else:
        print(frontier_mod.render_table(result))
    if out_path is not None:
        receipt_path = frontier_mod.write_receipt(result, out_path, limit=max(0, args.limit))
        print(f"wrote receipt → {relpath(receipt_path, base_root)}")
    return 0


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    import argparse

    parser = subparsers.add_parser(
        "frontier",
        help="Score backlog/tasks/facts to surface next coordinates",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of entries to show (default: 10)",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Optional path (relative to repo) to write receipt JSON",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
