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
        if "ts" not in record or "summary" not in record:
            print("::error ::memory/log.jsonl entries must include 'ts' and 'summary'")
            return 1

        # Canonical entries authored via tools.memory.write_log must include
        # the hash-linked fields and a run capsule identifier.
        if "run_id" in record or "hash_self" in record or "hash_prev" in record:
            for field in ("run_id", "hash_prev", "hash_self"):
                if field not in record:
                    print(f"::error ::canonical memory entry missing '{field}'")
                    return 1
            if record["hash_prev"] is not None and not isinstance(record["hash_prev"], str):
                print("::error ::'hash_prev' must be a string or null")
                return 1
            if not isinstance(record["hash_self"], str) or len(record["hash_self"]) != 64:
                print("::error ::'hash_self' must be a 64-character hex digest")
                return 1
            if not isinstance(record.get("run_id"), str) or not record["run_id"]:
                print("::error ::'run_id' must be a non-empty string")
                return 1

        # Legacy manual entries may include actor/ref/signatures; when present
        # ensure their types stay consistent for downstream tooling.
        if "artifacts" in record and not isinstance(record["artifacts"], list):
            print("::error ::'artifacts' must be a list when present")
            return 1
        if "receipts" in record and not isinstance(record["receipts"], list):
            print("::error ::'receipts' must be a list when present")
            return 1
        if "signatures" in record and not isinstance(record["signatures"], list):
            print("::error ::'signatures' must be a list when present")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
