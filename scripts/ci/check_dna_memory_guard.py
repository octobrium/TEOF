#!/usr/bin/env python3
"""Ensure DNA doc edits cite a recent memory observation receipt."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List

DNA_TARGETS = (
    "docs/architecture.md",
    "docs/workflow.md",
    "docs/promotion-policy.md",
)


def _git_diff_name_only(base: str) -> List[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def _git_show_lines(path: str, base: str) -> List[str]:
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


def _appended_entries(path: Path, base: str) -> List[dict]:
    previous = _git_show_lines(path.as_posix(), base)
    current = path.read_text(encoding="utf-8").splitlines()
    appended = current[len(previous) :] if previous else current
    records: List[dict] = []
    for line in appended:
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def main() -> int:
    base_sha = os.environ.get("BASE_SHA")
    if not base_sha:
        print("dna-memory-guard: BASE_SHA not set; skipping differential check.")
        return 0

    changed = _git_diff_name_only(base_sha)
    dna_changed = [path for path in DNA_TARGETS if path in changed]
    if not dna_changed:
        print("dna-memory-guard: no DNA docs changed.")
        return 0

    receipt_candidates = [
        Path(path) for path in changed if path.endswith("memory_guard/checks.jsonl")
    ]
    if not receipt_candidates:
        print(
            "::error ::DNA docs changed but no memory_guard/checks.jsonl receipts were updated. "
            "Run 'python -m tools.agent.session_guard log-memory-check --context dna' before committing."
        )
        return 1

    for receipt in receipt_candidates:
        if not receipt.exists():
            continue
        for record in _appended_entries(receipt, base_sha):
            if record.get("context") == "dna":
                return 0

    print(
        "::error ::DNA docs changed but no new memory_guard entries with context 'dna' were found. "
        "Log a memory observation before editing docs/architecture.md, docs/workflow.md, or docs/promotion-policy.md."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
