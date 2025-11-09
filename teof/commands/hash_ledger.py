from __future__ import annotations

from argparse import _SubParsersAction

from tools.autonomy import hash_ledger


def _dispatch(args) -> int:
    handler = getattr(args, "_hash_ledger_handler", None)
    if handler is None:
        raise SystemExit("hash_ledger: subcommand required (append|guard)")
    return handler(args)


def register(subparsers: "_SubParsersAction[object]") -> None:
    parser = subparsers.add_parser("hash_ledger", help="Manage hash-linked receipt ledger entries")
    hash_ledger.register_cli(parser)
    parser.set_defaults(func=_dispatch)
