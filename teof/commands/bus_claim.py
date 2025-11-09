from __future__ import annotations

import argparse

from tools.agent import bus_claim


def run(args: argparse.Namespace) -> int:
    """Execute bus_claim using the shared implementation."""
    return bus_claim.run_with_namespace(args)


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    """Register the `teof bus_claim` command."""
    parser = subparsers.add_parser(
        "bus_claim",
        help="Manage agent bus claims (claim/release)",
    )
    bus_claim.configure_parser(parser)
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
