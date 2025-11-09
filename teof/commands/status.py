from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from teof import status_report


def run(args: Namespace) -> int:
    out_path: Path | None = args.out
    quiet: bool = bool(getattr(args, "quiet", False))
    fmt = getattr(args, "format", "text").lower()
    root = status_report.ROOT
    log_flag = root.resolve() == status_report.ROOT.resolve()
    if out_path is not None:
        if not out_path.is_absolute():
            out_path = root / out_path
        status_report.write_status(out_path, root=root, quiet=quiet, format=fmt)
        return 0

    if fmt == "json":
        payload = status_report.build_status_payload(root, log=log_flag)
        content = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        content = status_report.generate_status(root, log=log_flag)
    if not quiet:
        print(content)
    else:
        print(content, end="")
    return 0


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    import argparse

    parser = subparsers.add_parser(
        "status",
        help="Generate repository status snapshot (default: print to stdout)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Write the status snapshot to this path instead of stdout",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress info logs (useful with --out)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
