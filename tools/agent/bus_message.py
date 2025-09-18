#!/usr/bin/env python3
"""Append structured messages to the agent coordination bus."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

ROOT = Path(__file__).resolve().parents[2]
MESSAGES_DIR = ROOT / "_bus" / "messages"
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


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


def _parse_meta(values: Iterable[str] | None) -> Dict[str, Any]:
    meta: Dict[str, Any] = {}
    if not values:
        return meta
    for item in values:
        key, sep, value = item.partition("=")
        if not sep:
            raise SystemExit(f"invalid --meta entry '{item}', expected key=value")
        key = key.strip()
        if not key:
            raise SystemExit("meta key must be non-empty")
        meta[key] = value
    return meta


def _append_message(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return path


def log_message(
    *,
    task_id: str,
    msg_type: str,
    summary: str,
    agent_id: Optional[str] = None,
    branch: Optional[str] = None,
    plan_id: Optional[str] = None,
    receipts: Optional[Iterable[str]] = None,
    meta: Optional[Mapping[str, Any]] = None,
    note: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> Path:
    if agent_id is None:
        agent_id = _default_agent()
    if not agent_id:
        raise SystemExit("agent id required; use --agent or populate AGENT_MANIFEST.json")

    payload: Dict[str, Any] = {
        "ts": timestamp or _iso_now(),
        "from": agent_id,
        "type": msg_type,
        "task_id": task_id,
        "summary": summary,
    }
    if branch:
        payload["branch"] = branch
    if plan_id:
        payload.setdefault("meta", {})["plan_id"] = plan_id
    if meta:
        payload.setdefault("meta", {}).update(meta)
    receipts_list = [r for r in (receipts or []) if r]
    if receipts_list:
        payload["receipts"] = receipts_list
    if note:
        payload["note"] = note

    path = MESSAGES_DIR / f"{task_id}.jsonl"
    return _append_message(path, payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append a message to the bus")
    parser.add_argument("--task", required=True, help="Task identifier (e.g., QUEUE-001)")
    parser.add_argument("--type", required=True, help="Message type (assignment, status, note, etc.)")
    parser.add_argument("--summary", required=True, help="Short message summary")
    parser.add_argument("--agent", help="Agent id (defaults to AGENT_MANIFEST)")
    parser.add_argument("--branch", help="Related branch (optional)")
    parser.add_argument("--plan", help="Related plan id (optional)")
    parser.add_argument("--receipt", action="append", help="Receipt path to attach (repeatable)")
    parser.add_argument("--meta", action="append", help="Additional key=value metadata (repeatable)")
    parser.add_argument("--note", help="Optional note to include in the message")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    meta = _parse_meta(args.meta)
    path = log_message(
        task_id=args.task,
        msg_type=args.type,
        summary=args.summary,
        agent_id=args.agent,
        branch=args.branch,
        plan_id=args.plan,
        receipts=args.receipt,
        meta=meta,
        note=args.note,
    )
    try:
        display_path = path.relative_to(ROOT)
    except ValueError:
        display_path = path
    print(f"Logged message to {display_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
