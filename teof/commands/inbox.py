from __future__ import annotations

import argparse
from pathlib import Path

from tools.agent import bus_inbox


def run(args: argparse.Namespace) -> int:
    """Execute the inbox helper using the shared bus_inbox CLI implementation."""
    return bus_inbox.run_cli(args)


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    """Attach the `teof inbox` command."""
    parser = subparsers.add_parser(
        "inbox",
        help="Inspect targeted agent inbox channels and capture receipts",
    )
    parser.add_argument("--agent", help="Agent id (defaults to AGENT_MANIFEST.json when omitted)")
    parser.add_argument(
        "--limit",
        type=int,
        default=bus_inbox.DEFAULT_LIMIT,
        help=f"Messages to capture (default: {bus_inbox.DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--mark-read",
        action="store_true",
        help="Update inbox state with the last seen message timestamp",
    )
    parser.add_argument(
        "--capture-receipt",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Write the inbox tail receipt (default: enabled)",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        help="Override the receipt path (default: _report/session/<agent>/agent-inbox-tail.txt)",
    )
    parser.add_argument(
        "--state",
        type=Path,
        help="Override the inbox state path (default: _report/session/<agent>/agent-inbox-state.json)",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
