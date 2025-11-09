from __future__ import annotations

import argparse

from tools.autonomy import macro_hygiene


def run(args: argparse.Namespace) -> int:
    return macro_hygiene.run_with_namespace(args)


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    parser = subparsers.add_parser(
        "macro_hygiene",
        help="Evaluate macro hygiene objectives and emit a status receipt",
    )
    macro_hygiene.configure_parser(parser)
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
