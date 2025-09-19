#!/usr/bin/env python3
"""Synchronize the local repo before starting an agent session."""
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[2]


class SessionSyncError(RuntimeError):
    """Base exception for session sync issues."""


class DirtyWorktreeError(SessionSyncError):
    """Raised when the working tree has uncommitted changes."""

    def __init__(self, status_output: str) -> None:
        message = "Working tree has local changes; commit/stash or rerun with --allow-dirty."
        super().__init__(message)
        self.status_output = status_output


class GitCommandError(SessionSyncError):
    """Raised when underlying git commands fail."""

    def __init__(self, command: Sequence[str], result: subprocess.CompletedProcess[str]) -> None:
        output = "\n".join(
            line
            for line in (result.stderr.strip(), result.stdout.strip())
            if line
        )
        if not output:
            output = "Unknown git error"
        message = f"git {' '.join(command)} failed: {output}"
        super().__init__(message)
        self.command = command
        self.result = result


@dataclass
class SyncResult:
    changed: bool
    fetch_output: str
    pull_output: str
    dirty: bool


def _run_git(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        raise GitCommandError(args, result)
    return result


def _status_porcelain() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def _combine_output(result: subprocess.CompletedProcess[str]) -> str:
    return "\n".join(
        line.strip()
        for line in (result.stdout, result.stderr)
        if line and line.strip()
    ).strip()


def _pull_applied_changes(output: str) -> bool:
    normalized = output.lower()
    if not normalized:
        return False
    if "already up to date" in normalized:
        return False
    if "already up-to-date" in normalized:
        return False
    return True


def run_sync(*, allow_dirty: bool = False) -> SyncResult:
    status_result = _status_porcelain()
    if status_result.returncode != 0:
        raise GitCommandError(["status", "--porcelain"], status_result)
    status_output = status_result.stdout.strip()
    dirty = bool(status_output)
    if dirty and not allow_dirty:
        raise DirtyWorktreeError(status_output)

    fetch_result = _run_git(["fetch", "--prune"])
    pull_result = _run_git(["pull", "--ff-only"])

    fetch_output = _combine_output(fetch_result)
    pull_output = _combine_output(pull_result)

    changed = _pull_applied_changes(pull_output)
    return SyncResult(changed=changed, fetch_output=fetch_output, pull_output=pull_output, dirty=dirty)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synchronize repo before agent session")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow sync to proceed even with local changes")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress git output, print only high-level summary",
    )
    return parser


def _emit_output(result: SyncResult) -> None:
    if result.fetch_output:
        for line in result.fetch_output.splitlines():
            print(f"git fetch | {line}")
    if result.pull_output:
        for line in result.pull_output.splitlines():
            print(f"git pull  | {line}")
    if not result.fetch_output and not result.pull_output:
        print("git sync   | no output")


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        result = run_sync(allow_dirty=args.allow_dirty)
    except SessionSyncError as exc:
        print(f"Session sync failed: {exc}", file=sys.stderr)
        return 1

    if args.quiet:
        summary = "updates applied" if result.changed else "already up to date"
        print(f"Session sync succeeded ({summary}).")
    else:
        _emit_output(result)
        if result.changed:
            print("Session sync succeeded: updates applied.")
        else:
            print("Session sync succeeded: repository already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
