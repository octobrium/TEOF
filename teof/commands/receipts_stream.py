from __future__ import annotations

import argparse
from pathlib import Path

from tools.autonomy import receipts_index_stream as ris


def run(args: argparse.Namespace) -> int:
    return ris.cmd_stream(args)


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    parser = subparsers.add_parser(
        "receipts_stream",
        help="Down-sample the receipts index into hashed shards with a latest pointer",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ris.DEFAULT_MANIFEST,
        help=f"Path to receipts-index manifest.json (default: {ris.DEFAULT_MANIFEST.relative_to(ris.ROOT)})",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=ris.DEFAULT_DEST,
        help=f"Directory for shard JSONL files (default: {ris.DEFAULT_DEST.relative_to(ris.ROOT)})",
    )
    parser.add_argument(
        "--pointer",
        type=Path,
        default=ris.DEFAULT_POINTER,
        help=f"Pointer file capturing the latest shard (default: {ris.DEFAULT_POINTER.relative_to(ris.ROOT)})",
    )
    parser.add_argument(
        "--max-entries",
        type=int,
        default=ris.DEFAULT_MAX_ENTRIES,
        help=f"Maximum entries per shard (default: {ris.DEFAULT_MAX_ENTRIES})",
    )
    parser.add_argument(
        "--since-shard",
        help="Optional shard id from which to resume (inclusive)",
    )
    parser.add_argument(
        "--max-age-hours",
        type=float,
        default=float(ris.DEFAULT_MAX_AGE_HOURS),
        help=f"Fail when latest entry is older than this threshold (default: {ris.DEFAULT_MAX_AGE_HOURS}h)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate shard creation without writing pointer updates",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        help="Optional JSON receipt path summarizing the stream run",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
