#!/usr/bin/env python3
"""Append structured messages to the agent coordination bus."""
from __future__ import annotations

import argparse
import json
import re
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
TARGET_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


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


def _normalize_target(target: str | None) -> str | None:
    if target is None:
        return None
    candidate = target.strip().lower()
    if not candidate:
        raise SystemExit("--target requires a non-empty agent id")
    if "/" in candidate or "\\" in candidate:
        raise SystemExit("--target must not contain path separators")
    if not TARGET_PATTERN.fullmatch(candidate):
        raise SystemExit("--target must contain only alphanumeric, dot, underscore, or hyphen characters")
    if candidate.startswith("."):
        raise SystemExit("--target must not start with '.'")
    return candidate


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
    target: Optional[str] = None,
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
    target_slug = _normalize_target(target)
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
    if target_slug:
        payload["to"] = target_slug

    path = MESSAGES_DIR / f"{task_id}.jsonl"
    result = _append_message(path, payload)

    if target_slug:
        agent_payload = dict(payload)
        agent_path = MESSAGES_DIR / f"agent-{target_slug}.jsonl"
        _append_message(agent_path, agent_payload)

    record_usage(
        "bus_message",
        action=msg_type,
        extra={
            "task": task_id,
            "agent": agent_id,
            **({"target": target_slug} if target_slug else {}),
        },
    )
    return result


def configure_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
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
        "--target",
        help="Agent role to notify (writes `_bus/messages/agent-<role>.jsonl` in addition to the task lane)",
    )
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append a message to the bus")
    configure_parser(parser)
    return parser


def run_with_namespace(args: argparse.Namespace, *, parser: argparse.ArgumentParser | None = None) -> int:
    meta = _parse_meta(getattr(args, "meta", None))
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
        target=args.target,
    )

    try:
        display_path = path.relative_to(ROOT)
    except ValueError:
        display_path = path

    if args.target:
        target_slug = _normalize_target(args.target)
        target_path = MESSAGES_DIR / f"agent-{target_slug}.jsonl"
        try:
            target_display = target_path.relative_to(ROOT)
        except ValueError:
            target_display = target_path
        print(f"Logged message to {display_path} + agent inbox {target_display}")
    else:
        print(f"Logged message to {display_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_with_namespace(args, parser=parser)


if __name__ == "__main__":
    sys.exit(main())
