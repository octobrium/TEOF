from __future__ import annotations

import argparse

from tools.impact import bridge


def run(args: argparse.Namespace) -> int:
    return bridge.run_with_namespace(args)


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    parser = subparsers.add_parser(
        "impact_bridge",
        help="Summarize how impact ledger entries connect to backlog items",
    )
    bridge.configure_parser(parser)
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
