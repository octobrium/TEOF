#!/usr/bin/env python3
"""Summarize the agent coordination bus."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CLAIMS_DIR = ROOT / "_bus" / "claims"
EVENT_LOG = ROOT / "_bus" / "events" / "events.jsonl"


def load_claims() -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    if not CLAIMS_DIR.exists():
        return claims
    for path in sorted(CLAIMS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
        data["_path"] = path.relative_to(ROOT).as_posix()
        claims.append(data)
    return claims


def load_events(limit: int | None = None) -> list[dict[str, Any]]:
    if not EVENT_LOG.exists():
        return []
    events: list[dict[str, Any]] = []
    with EVENT_LOG.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON in events log: {exc}") from exc
    if limit is not None:
        events = events[-limit:]
    for idx, entry in enumerate(events):
        entry["_index"] = len(events) - idx
    return events


def summarize(claims: list[dict[str, Any]], events: list[dict[str, Any]]) -> None:
    if claims:
        print("Active claims:")
        for claim in claims:
            status = claim.get("status", "unknown")
            print(
                f"  - {claim.get('task_id')} [{status}] by {claim.get('agent_id')}"
                f" → {claim.get('branch')} (plan={claim.get('plan_id', 'N/A')})"
            )
    else:
        print("No claims recorded.")

    if events:
        print("\nRecent events:")
        for entry in events:
            task = entry.get("task_id", "-")
            summary = entry.get("summary", "")
            print(
                f"  - {entry.get('ts')} :: {entry.get('agent_id')} :: {entry.get('event')}"
                f" :: task={task} :: {summary}"
            )
    else:
        print("\nNo events recorded.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize the agent bus state")
    parser.add_argument("--limit", type=int, default=10, help="Number of recent events to display")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    claims = load_claims()
    events = load_events(limit=args.limit)
    summarize(claims, events)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
