#!/usr/bin/env python3
"""Aggregate reconciliation metrics JSONL into a summary report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_entries(path: Path) -> list[dict]:
    entries = []
    if not path.exists():
        return entries
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def summarize(entries: list[dict]) -> dict:
    total = len(entries)
    matches = sum(1 for e in entries if e.get("matches"))
    diff_total = sum(int(e.get("difference_count", 0)) for e in entries)
    missing_total = sum(int(e.get("missing_receipt_count", 0)) for e in entries)
    capability_total = sum(int(e.get("capability_diff_count", 0)) for e in entries)
    return {
        "total_runs": total,
        "match_ratio": (matches / total) if total else None,
        "difference_total": diff_total,
        "missing_receipt_total": missing_total,
        "capability_diff_total": capability_total,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize metrics JSONL")
    parser.add_argument("metrics_file", help="Path to metrics JSONL")
    args = parser.parse_args()

    entries = load_entries(Path(args.metrics_file))
    summary = summarize(entries)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
