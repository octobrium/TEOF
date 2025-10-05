#!/usr/bin/env python3
"""Emit a standard coordination heartbeat via bus_event (and optional bus_message)."""
from __future__ import annotations

import argparse
from typing import Iterable

from tools.agent import bus_event, bus_message, session_guard


from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"


DEFAULT_EVENT = "status"
DEFAULT_MESSAGE_TYPE = "status"


def _ensure_prefix(agent_id: str, summary: str) -> str:
    summary = summary.strip() or "heartbeat"
    prefix = f"{agent_id}:"
    if summary.lower().startswith(prefix.lower()):
        return summary
    return f"{agent_id}: {summary}"


def _build_event_args(
    *,
    summary: str,
    agent: str | None,
    event: str,
    task: str | None,
    plan: str | None,
    branch: str | None,
    pr: str | None,
    receipt: str | None,
) -> list[str]:
    argv: list[str] = [
        "log",
        "--event",
        event,
        "--summary",
        summary,
    ]
    if task:
        argv += ["--task", task]
    if plan:
        argv += ["--plan", plan]
    if branch:
        argv += ["--branch", branch]
    if pr:
        argv += ["--pr", pr]
    if receipt:
        argv += ["--receipt", receipt]
    if agent:
        argv += ["--agent", agent]
    return argv


def _build_message_args(
    *,
    task: str,
    msg_type: str,
    summary: str,
    agent: str | None,
    note: str | None,
    receipts: Iterable[str] | None,
    meta: Iterable[str] | None,
) -> list[str]:
    argv: list[str] = [
        "--task",
        task,
        "--type",
        msg_type,
        "--summary",
        summary,
    ]
    if agent:
        argv += ["--agent", agent]
    if note:
        argv += ["--note", note]
    for receipt in receipts or []:
        argv += ["--receipt", receipt]
    for item in meta or []:
        argv += ["--meta", item]
    return argv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit a standard bus heartbeat")
    parser.add_argument("--summary", help="Summary text (without agent prefix)")
    parser.add_argument("--event", default=DEFAULT_EVENT, help="Event type for bus_event (default: status)")
    parser.add_argument("--task", help="Task id for bus_event")
    parser.add_argument("--plan", help="Plan id for the heartbeat")
    parser.add_argument("--branch", help="Branch name for context")
    parser.add_argument("--pr", help="Associated PR number")
    parser.add_argument("--event-receipt", dest="event_receipt", help="Receipt path to attach to the event")
    parser.add_argument("--agent", help="Override agent id (defaults to manifest)")
    parser.add_argument("--skip-event", action="store_true", help="Skip logging the bus_event heartbeat")

    parser.add_argument(
        "--message-task",
        help="Optional task id to also append a bus_message status",
    )
    parser.add_argument(
        "--message-type",
        default=DEFAULT_MESSAGE_TYPE,
        help="Message type for bus_message (default: status)",
    )
    parser.add_argument("--note", help="Optional note for the bus message")
    parser.add_argument(
        "--message-receipt",
        action="append",
        help="Attach receipt(s) to the bus message",
    )
    parser.add_argument(
        "--message-meta",
        action="append",
        help="Additional key=value metadata for the bus message",
    )
    parser.add_argument(
        "--skip-message",
        action="store_true",
        help="Skip posting the optional bus_message even if --message-task is supplied",
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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    agent_id = session_guard.resolve_agent_id(args.agent, manifest_path=MANIFEST_PATH)
    session_guard.ensure_recent_session(
        agent_id,
        allow_stale=args.allow_stale_session,
        max_age_seconds=args.session_max_age,
        context="bus_ping",
    )

    summary = _ensure_prefix(agent_id, args.summary or "heartbeat")

    if not args.skip_event:
        event_argv = _build_event_args(
            summary=summary,
            agent=agent_id,
            event=args.event,
            task=args.task,
            plan=args.plan,
            branch=args.branch,
            pr=args.pr,
            receipt=args.event_receipt,
        )
        if args.allow_stale_session:
            event_argv += ["--allow-stale-session"]
        if args.session_max_age is not None:
            event_argv += ["--session-max-age", str(args.session_max_age)]
        rc = bus_event.main(event_argv)
        if rc != 0:
            return rc

    if args.message_task and not args.skip_message:
        message_argv = _build_message_args(
            task=args.message_task,
            msg_type=args.message_type,
            summary=summary,
            agent=agent_id,
            note=args.note,
            receipts=args.message_receipt,
            meta=args.message_meta,
        )
        if args.allow_stale_session:
            message_argv += ["--allow-stale-session"]
        if args.session_max_age is not None:
            message_argv += ["--session-max-age", str(args.session_max_age)]
        rc = bus_message.main(message_argv)
        if rc != 0:
            return rc

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
