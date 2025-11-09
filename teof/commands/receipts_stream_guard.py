from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.autonomy import receipts_stream_guard as guard


def _resolve_repo_path(path: Path) -> Path:
    return path if path.is_absolute() else guard.ROOT / path


def run(args: argparse.Namespace) -> int:
    pointer = _resolve_repo_path(args.pointer)
    max_age = args.max_age_hours if args.max_age_hours > 0 else None
    receipt = _resolve_repo_path(args.receipt) if args.receipt else None
    try:
        message = guard.run(pointer=pointer, max_age_hours=max_age, receipt=receipt)
    except guard.GuardError as exc:
        if receipt is not None:
            guard.record_failure(pointer, receipt, str(exc))
        print(f"receipts_stream_guard: {exc}", file=sys.stderr)
        return 1
    print(message)
    return 0


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    parser = subparsers.add_parser(
        "receipts_stream_guard",
        help="Verify receipts stream pointer integrity/freshness",
    )
    parser.add_argument(
        "--pointer",
        type=Path,
        default=guard.DEFAULT_POINTER.relative_to(guard.ROOT),
        help=f"Pointer file to validate (default: {guard.DEFAULT_POINTER.relative_to(guard.ROOT)})",
    )
    parser.add_argument(
        "--max-age-hours",
        type=float,
        default=guard.DEFAULT_MAX_AGE_HOURS,
        help="Fail when latest shard age exceeds this threshold (set <=0 to disable)",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        help="Optional JSON receipt capturing guard status",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
