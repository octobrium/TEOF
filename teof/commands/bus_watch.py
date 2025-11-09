from __future__ import annotations

import argparse

from tools.agent import bus_watch


def run(args: argparse.Namespace) -> int:
    """Execute bus_watch using the shared implementation."""
    return bus_watch.run_with_namespace(args)


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    """Register the `teof bus_watch` command."""
    parser = subparsers.add_parser(
        "bus_watch",
        help="Tail agent bus events with optional filters/follow mode",
    )
    bus_watch.configure_parser(parser)
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
