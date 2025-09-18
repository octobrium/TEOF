#!/usr/bin/env python3
"""Append events to the agent coordination bus."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EVENT_LOG = ROOT / "_bus" / "events" / "events.jsonl"
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"


REQUIRED_FIELDS = {"ts", "agent_id", "event", "summary"}


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_agent() -> str | None:
    if not MANIFEST_PATH.exists():
        return None
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    agent_id = data.get("agent_id")
    if isinstance(agent_id, str) and agent_id.strip():
        return agent_id.strip()
    return None


def _append_event(payload: dict[str, Any]) -> None:
    EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with EVENT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def handle_log(args: argparse.Namespace) -> None:
    agent_id = args.agent or _default_agent()
    if not agent_id:
        raise SystemExit("agent id required (supply --agent or populate AGENT_MANIFEST.json)")

    payload: dict[str, Any] = {
        "ts": _iso_now(),
        "agent_id": agent_id,
        "event": args.event,
        "summary": args.summary,
    }
    if args.task:
        payload["task_id"] = args.task
    if args.plan:
        payload["plan_id"] = args.plan
    if args.branch:
        payload["branch"] = args.branch
    if args.pr:
        payload["pr"] = args.pr
    if args.receipt:
        payload.setdefault("receipts", []).append(args.receipt)
    if args.extra:
        for item in args.extra:
            key, _, value = item.partition("=")
            if not key or not value:
                raise SystemExit(f"invalid extra field '{item}', expected key=value")
            payload[key] = value

    _append_event(payload)
    print(f"Logged event {args.event} for agent {agent_id}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append coordination events")
    sub = parser.add_subparsers(dest="command", required=True)

    log = sub.add_parser("log", help="Append an event")
    log.add_argument("--event", required=True, help="Event type (claim, proposal, pr_opened, etc.)")
    log.add_argument("--summary", required=True, help="Short description")
    log.add_argument("--task", help="Task identifier")
    log.add_argument("--plan", help="Plan identifier")
    log.add_argument("--branch", help="Branch name")
    log.add_argument("--pr", help="Associated PR number")
    log.add_argument("--receipt", help="Receipt path to record")
    log.add_argument("--agent", help="Agent id (defaults to manifest)")
    log.add_argument("--extra", nargs="*", help="Additional key=value pairs")
    log.set_defaults(func=handle_log)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except AttributeError:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
