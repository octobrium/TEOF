#!/usr/bin/env python3
"""Query memory/log.jsonl entries."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parents[2] / "memory" / "log.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Display recent memory entries")
    parser.add_argument("--limit", type=int, default=5, help="Number of entries to display")
    parser.add_argument("--actor", help="Filter by actor", default=None)
    parser.add_argument("--ref", help="Filter by ref substring", default=None)
    return parser.parse_args()


def load_entries() -> list[dict]:
    entries: list[dict] = []
    with LOG_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


def format_entry(entry: dict) -> str:
    artifacts = ", ".join(entry.get("artifacts", [])) or "-"
    signatures = ", ".join(entry.get("signatures", [])) or "-"
    return (
        f"{entry['ts']} | {entry['actor']} | {entry['summary']}\n"
        f"  ref: {entry['ref']}\n"
        f"  artifacts: {artifacts}\n"
        f"  signatures: {signatures}"
    )


def main() -> None:
    if not LOG_PATH.exists():
        raise SystemExit("memory/log.jsonl missing")

    args = parse_args()
    entries = load_entries()

    filtered = []
    for entry in reversed(entries):  # newest first
        if args.actor and entry.get("actor") != args.actor:
            continue
        if args.ref and args.ref not in entry.get("ref", ""):
            continue
        filtered.append(entry)
        if len(filtered) >= args.limit:
            break

    if not filtered:
        print("No entries found")
        return

    for entry in filtered:
        print(format_entry(entry))
        print()


if __name__ == "__main__":
    main()
