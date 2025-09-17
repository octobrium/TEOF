#!/usr/bin/env python3
"""Maintain and query a hot index for memory/log.jsonl."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List, Dict

ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = ROOT / "memory" / "log.jsonl"
INDEX_PATH = ROOT / "memory" / "hot_index.json"


def load_entries(limit: int | None = None) -> List[Dict]:
    entries: list[dict] = []
    with LOG_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    if limit:
        entries = entries[-limit:]
    return entries


def cmd_build(args: argparse.Namespace) -> int:
    entries = load_entries(limit=args.limit)
    INDEX_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} entries to {INDEX_PATH.relative_to(ROOT)}")
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    if args.use_index and INDEX_PATH.exists():
        entries = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    else:
        entries = load_entries()
    filtered = []
    for entry in reversed(entries):
        if args.actor and entry.get("actor") != args.actor:
            continue
        if args.ref and args.ref not in entry.get("ref", ""):
            continue
        filtered.append(entry)
        if len(filtered) >= args.limit:
            break
    output(entries=filtered, json_output=args.json)
    return 0


def output(entries: Iterable[dict], json_output: bool) -> None:
    entries = list(entries)
    if json_output:
        json.dump(entries, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return
    if not entries:
        print("No entries found")
        return
    for entry in entries:
        artifacts = ", ".join(entry.get("artifacts", [])) or "-"
        signatures = ", ".join(entry.get("signatures", [])) or "-"
        print(f"{entry['ts']} | {entry['actor']} | {entry['summary']}")
        print(f"  ref: {entry['ref']}")
        print(f"  artifacts: {artifacts}")
        print(f"  signatures: {signatures}")
        print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hot index helper for memory/log.jsonl")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Write an index file with the latest entries")
    build.add_argument("--limit", type=int, default=100)
    build.set_defaults(func=cmd_build)

    query = sub.add_parser("query", help="Query entries, optionally using the hot index")
    query.add_argument("--limit", type=int, default=10)
    query.add_argument("--actor")
    query.add_argument("--ref")
    query.add_argument("--json", action="store_true")
    query.add_argument("--use-index", action="store_true")
    query.set_defaults(func=cmd_query)

    return parser


def main() -> int:
    if not LOG_PATH.exists():
        print("memory/log.jsonl missing", file=sys.stderr)
        return 1
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
