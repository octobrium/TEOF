#!/usr/bin/env python3
"""Fail when the worktree carries more changes than expected."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable

DEFAULT_MAX_CHANGES = 60


def _git_status(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "git status failed (return code {})".format(result.returncode)
        )
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return lines


def _format_sample(changes: Iterable[str], limit: int = 10) -> str:
    sample = []
    for change in changes:
        sample.append(change[3:] if len(change) > 3 else change)
        if len(sample) >= limit:
            break
    return ", ".join(sample)


def check_worktree(*, root: Path, max_changes: int) -> int:
    changes = _git_status(root)
    total = len(changes)
    if total > max_changes:
        print(
            "Worktree has {} tracked/untracked changes (max {}).".format(
                total, max_changes
            ),
            file=sys.stderr,
        )
        if changes:
            print(
                "Examples: {}".format(_format_sample(changes)),
                file=sys.stderr,
            )
        return 1
    print(
        "Worktree clean enough: {} ≤ {} changes.".format(total, max_changes)
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: cwd)",
    )
    parser.add_argument(
        "--max-changes",
        type=int,
        default=DEFAULT_MAX_CHANGES,
        help="Maximum allowed changes before failing (default: %(default)s)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return check_worktree(root=args.root, max_changes=args.max_changes)
    except RuntimeError as exc:
        print(f"worktree guard error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
