#!/usr/bin/env python3
"""Append structured messages to the agent coordination bus."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

from tools.agent.claim_guard import ensure_claim_owner
from tools.agent import session_guard
from tools.usage.logger import record_usage

ROOT = Path(__file__).resolve().parents[2]
MESSAGES_DIR = ROOT / "_bus" / "messages"
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"
CLAIMS_DIR = ROOT / "_bus" / "claims"
AGENT_REPORT_DIR = ROOT / "_report" / "agent"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
GUARDED_MESSAGE_TYPES = {"status", "note", "request", "summary", "consensus", "proposal"}


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


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
    allow_stale_session: bool = False,
    session_max_age: Optional[int] = None,
    context: str = "bus_message",
) -> Path:
    agent_id = session_guard.resolve_agent_id(agent_id, manifest_path=MANIFEST_PATH)
    session_guard.ensure_recent_session(
        agent_id,
        allow_stale=allow_stale_session,
        max_age_seconds=session_max_age,
        context=context,
    )

    if task_id and msg_type in GUARDED_MESSAGE_TYPES:
        ensure_claim_owner(
            claims_dir=CLAIMS_DIR,
            report_root=AGENT_REPORT_DIR,
            agent_id=agent_id,
            task_id=task_id,
            action=msg_type,
        )

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
    result = _append_message(path, payload)
    record_usage(
        "bus_message",
        action=msg_type,
        extra={
            "task": task_id,
            "agent": agent_id,
        },
    )
    return result


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
    parser.add_argument(
        "--allow-stale-session",
        action="store_true",
        help="Bypass session freshness guard (logs override receipt)",
    )
    parser.add_argument(
        "--session-max-age",
        type=int,
        help="Override session freshness limit in seconds (default: env TEOF_SESSION_MAX_AGE or 3600)",
    )
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
        allow_stale_session=args.allow_stale_session,
        session_max_age=args.session_max_age,
    )
    try:
        display_path = path.relative_to(ROOT)
    except ValueError:
        display_path = path
    print(f"Logged message to {display_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
