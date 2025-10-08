from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List

from tools.impact import ttd_trend as ttd_trend_mod

from ._utils import module_root


def run(args: Namespace) -> int:
    argv: List[str] = ["--window", str(args.window), "--format", args.format]
    base_root = module_root(ttd_trend_mod)
    if args.input is not None:
        input_path = args.input if args.input.is_absolute() else base_root / args.input
        argv.extend(["--input", str(input_path)])
    if args.days is not None:
        argv.extend(["--days", str(args.days)])
    if args.out is not None:
        out_path = args.out if args.out.is_absolute() else base_root / args.out
        argv.extend(["--out", str(out_path)])
    return ttd_trend_mod.main(argv)


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    import argparse

    parser = subparsers.add_parser(
        "ttd-trend",
        help="Analyse TTΔ history and emit trend summaries",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Override path to ttd.jsonl (default: memory/impact/ttd.jsonl)",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=14,
        help="Number of recent entries to analyse (default: 14)",
    )
    parser.add_argument(
        "--days",
        type=float,
        help="Optional time window in days for analysis",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Optional path to write JSON summary",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
