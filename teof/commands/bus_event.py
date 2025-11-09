from __future__ import annotations

import argparse

from tools.agent import bus_event


def run(args: argparse.Namespace) -> int:
    handler = getattr(args, "handler", None)
    if handler is None:
        print("bus_event: missing subcommand (e.g., log)", flush=True)
        return 1
    handler(args)
    return 0


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    parser = subparsers.add_parser(
        "bus_event",
        help="Append coordination events (teof wrapper)",
    )
    bus_event.configure_parser(parser)
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
