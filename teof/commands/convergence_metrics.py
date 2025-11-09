from __future__ import annotations

from tools.network import convergence_metrics as cm


def run(args) -> int:
    return args.func(args)


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    parser = subparsers.add_parser(
        "convergence_metrics",
        help="Collect, aggregate, and guard convergence metrics",
    )
    cm.configure_subparser(parser)
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
