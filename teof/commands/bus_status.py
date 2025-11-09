from __future__ import annotations

import argparse

from tools.agent import bus_status


def run(args: argparse.Namespace) -> int:
    """Execute bus_status using the shared implementation."""
    return bus_status.run_with_namespace(args)


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    """Register the `teof bus_status` command."""
    parser = subparsers.add_parser(
        "bus_status",
        help="Summarize the agent bus (claims, events, manager heartbeat)",
    )
    bus_status.configure_parser(parser)
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
