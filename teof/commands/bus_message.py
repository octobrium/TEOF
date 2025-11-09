from __future__ import annotations

import argparse

from tools.agent import bus_message


def run(args: argparse.Namespace) -> int:
    return bus_message.run_with_namespace(args)


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    parser = subparsers.add_parser(
        "bus_message",
        help="Append structured messages to the agent bus",
    )
    bus_message.configure_parser(parser)
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
