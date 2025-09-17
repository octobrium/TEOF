#!/usr/bin/env python3
"""Verify append-only memory log policy for memory/log.jsonl."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

WATCH_PREFIXES = (
    "extensions/",
    "tools/",
    "scripts/",
    "docs/",
)
LOG_PATH = Path("memory/log.jsonl")


def _git_diff_name_only(base: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def _git_show(path: str, base: str) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "show", f"{base}:{path}"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.splitlines()
    except subprocess.CalledProcessError:
        return []


def main() -> int:
    base_sha = os.environ.get("BASE_SHA")
    if not base_sha:
        print("BASE_SHA not provided", file=sys.stderr)
        return 2

    if not LOG_PATH.exists():
        print("::error ::memory/log.jsonl missing")
        return 1

    changed_paths = _git_diff_name_only(base_sha)
    watched_changes = [p for p in changed_paths if any(p.startswith(prefix) for prefix in WATCH_PREFIXES) and not p.startswith("docs/policy/") and not p.startswith("docs/deploy/") and p != "memory/log.jsonl"]

    log_changed = "memory/log.jsonl" in changed_paths
    if watched_changes and not log_changed:
        print("::error ::changes detected but memory/log.jsonl not updated")
        return 1

    old_lines = _git_show("memory/log.jsonl", base_sha)
    new_lines = LOG_PATH.read_text(encoding="utf-8").splitlines()

    if old_lines:
        if len(new_lines) < len(old_lines) or new_lines[: len(old_lines)] != old_lines:
            print("::error ::memory/log.jsonl must be append-only")
            return 1
    elif not new_lines:
        print("::error ::memory/log.jsonl cannot be empty")
        return 1

    appended = new_lines[len(old_lines) :] if old_lines else new_lines
    for line in appended:
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"::error ::invalid JSON line in memory/log.jsonl: {exc}")
            return 1
        for field in ("ts", "actor", "summary", "ref", "artifacts", "signatures"):
            if field not in record:
                print(f"::error ::missing '{field}' in memory/log.jsonl entry")
                return 1
        if not isinstance(record.get("artifacts"), list) or not isinstance(record.get("signatures"), list):
            print("::error ::'artifacts' and 'signatures' must be lists")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
