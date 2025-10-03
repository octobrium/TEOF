#!/usr/bin/env python3
"""Helpers for listing and clearing git assume-unchanged flags."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[2]


def _run(cmd: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=True)


def _ls_files() -> list[str]:
    result = _run(["git", "ls-files", "-v"])
    return result.stdout.splitlines()


def list_flags() -> list[str]:
    flagged: list[str] = []
    for line in _ls_files():
        if not line:
            continue
        status, _, path = line.partition(" ")
        if status and status[0].islower() and path:
            flagged.append(path)
    return flagged


def clear_flags(paths: Iterable[str]) -> None:
    items = list(paths)
    if not items:
        return
    _run(["git", "update-index", "--no-assume-unchanged", *items])


def cmd_list(_: argparse.Namespace) -> int:
    flagged = list_flags()
    if not flagged:
        print("No files are marked assume-unchanged.")
        return 0
    print("Files marked assume-unchanged (clear with `python -m tools.agent.reset_assume_unchanged clear`):")
    for path in flagged:
        print(f"  {path}")
    return 0


def cmd_clear(_: argparse.Namespace) -> int:
    flagged = list_flags()
    if not flagged:
        print("Nothing to clear; no files are marked assume-unchanged.")
        return 0
    clear_flags(flagged)
    print(f"Cleared assume-unchanged flag on {len(flagged)} file(s).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.agent.reset_assume_unchanged",
        description="List or clear files marked assume-unchanged",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="List files flagged assume-unchanged")
    list_cmd.set_defaults(func=cmd_list)

    clear_cmd = sub.add_parser("clear", help="Remove assume-unchanged flag from all files")
    clear_cmd.set_defaults(func=cmd_clear)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
