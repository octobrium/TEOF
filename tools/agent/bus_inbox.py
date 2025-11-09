#!/usr/bin/env python3
"""Inspect and capture per-agent inbox tails."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Mapping

from tools.agent import session_guard

ROOT = Path(__file__).resolve().parents[2]
MESSAGES_DIR = ROOT / "_bus" / "messages"
SESSION_REPORT_DIR = ROOT / "_report" / "session"
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
DEFAULT_LIMIT = 10


class BusInboxError(RuntimeError):
    """Raised when inbox inspection fails."""


@dataclass
class InboxSummary:
    agent_id: str
    channel_path: Path
    total_messages: int
    new_messages: int
    last_message_ts: str | None
    receipt_path: Path | None
    state_path: Path


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


def _parse_iso(ts: object) -> datetime | None:
    if not isinstance(ts, str):
        return None
    try:
        return datetime.strptime(ts, ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _normalize_agent(agent_id: str) -> str:
    slug = agent_id.strip().lower()
    if not slug:
        raise BusInboxError("agent id missing")
    if slug.startswith(".") or "/" in slug or "\\" in slug:
        raise BusInboxError(f"invalid agent id '{agent_id}' for inbox channel")
    return slug


def _channel_path(agent_id: str) -> Path:
    return MESSAGES_DIR / f"agent-{_normalize_agent(agent_id)}.jsonl"


def _default_receipt_path(agent_id: str) -> Path:
    return SESSION_REPORT_DIR / agent_id / "agent-inbox-tail.txt"


def _default_state_path(agent_id: str) -> Path:
    return SESSION_REPORT_DIR / agent_id / "agent-inbox-state.json"


def _load_messages(path: Path) -> list[Mapping[str, object]]:
    if not path.exists():
        return []
    entries: list[Mapping[str, object]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, Mapping):
                entries.append(payload)
    return entries


def _load_state(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    result: dict[str, str] = {}
    last_seen = data.get("last_seen_ts")
    if isinstance(last_seen, str):
        result["last_seen_ts"] = last_seen
    return result


def _write_state(path: Path, *, last_seen_ts: str | None, previous: dict[str, str]) -> None:
    payload: dict[str, object] = {
        "last_checked_at": _iso_now(),
    }
    final_seen = last_seen_ts or previous.get("last_seen_ts")
    if final_seen:
        payload["last_seen_ts"] = final_seen
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _count_new(messages: list[Mapping[str, object]], last_seen_ts: str | None) -> int:
    if not messages:
        return 0
    if not last_seen_ts:
        return len(messages)
    cutoff = _parse_iso(last_seen_ts)
    if cutoff is None:
        return len(messages)
    count = 0
    for payload in messages:
        ts = _parse_iso(payload.get("ts"))
        if ts and ts > cutoff:
            count += 1
    return count


def _write_receipt(
    path: Path,
    *,
    agent_id: str,
    channel_path: Path,
    tail: List[Mapping[str, object]],
    limit: int,
    unread: int,
    last_ts: str | None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rel_channel = channel_path
    try:
        rel_channel = channel_path.relative_to(ROOT)
    except ValueError:
        pass
    header = (
        "# agent inbox tail\n"
        f"# agent={agent_id}\n"
        f"# channel={rel_channel}\n"
        f"# captured_at={_iso_now()}\n"
        f"# requested_entries={max(limit, 0)}\n"
        f"# written_entries={len(tail)}\n"
        f"# unread_since_state={unread}\n"
        f"# last_message_ts={last_ts or '-'}\n\n"
    )
    with path.open("w", encoding="utf-8") as fh:
        fh.write(header)
        for payload in tail:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
        if not tail:
            fh.write("(inbox empty)\n")
    return path


def inspect_inbox(
    *,
    agent_id: str | None = None,
    limit: int = DEFAULT_LIMIT,
    receipt_path: Path | None = None,
    state_path: Path | None = None,
    mark_read: bool = False,
    capture_receipt: bool = True,
    enforce_manifest: bool = True,
) -> InboxSummary:
    if enforce_manifest:
        resolved_agent = session_guard.resolve_agent_id(agent_id, manifest_path=MANIFEST_PATH)
    else:
        candidate = (agent_id or "").strip()
        if candidate:
            resolved_agent = candidate
        else:
            resolved_agent = session_guard.resolve_agent_id(None, manifest_path=MANIFEST_PATH)
    if limit < 0:
        raise BusInboxError("--limit must be >= 0")
    channel_path = _channel_path(resolved_agent)
    messages = _load_messages(channel_path)
    last_ts = messages[-1].get("ts") if messages else None  # type: ignore[assignment]
    tail = messages[-limit:] if limit and len(messages) > limit else list(messages)

    state_path = state_path or _default_state_path(resolved_agent)
    state = _load_state(state_path)
    last_seen_ts = state.get("last_seen_ts")
    new_messages = _count_new(messages, last_seen_ts)

    receipt: Path | None = None
    if capture_receipt:
        receipt = _write_receipt(
            receipt_path or _default_receipt_path(resolved_agent),
            agent_id=resolved_agent,
            channel_path=channel_path,
            tail=tail,
            limit=limit,
            unread=new_messages,
            last_ts=last_ts if isinstance(last_ts, str) else None,
        )

    if mark_read:
        _write_state(
            state_path,
            last_seen_ts=last_ts if isinstance(last_ts, str) else None,
            previous=state,
        )

    return InboxSummary(
        agent_id=resolved_agent,
        channel_path=channel_path,
        total_messages=len(messages),
        new_messages=new_messages,
        last_message_ts=last_ts if isinstance(last_ts, str) else None,
        receipt_path=receipt,
        state_path=state_path,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tail the agent inbox channel and record receipts")
    parser.add_argument("--agent", help="Agent id (defaults to AGENT_MANIFEST.json)")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Messages to capture (default: %(default)s)")
    parser.add_argument(
        "--mark-read",
        action="store_true",
        help="Update inbox state with the last seen message timestamp",
    )
    parser.add_argument(
        "--capture-receipt",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Write the inbox tail receipt (default: enabled)",
    )
    parser.add_argument(
        "--receipt",
        help="Override the receipt path (default: _report/session/<agent>/agent-inbox-tail.txt)",
    )
    parser.add_argument(
        "--state",
        help="Override the inbox state path (default: _report/session/<agent>/agent-inbox-state.json)",
    )
    return parser


def run_cli(args: argparse.Namespace) -> int:
    receipt_arg = getattr(args, "receipt", None)
    state_arg = getattr(args, "state", None)
    receipt_path = Path(receipt_arg) if receipt_arg else None
    state_path = Path(state_arg) if state_arg else None
    try:
        summary = inspect_inbox(
            agent_id=getattr(args, "agent", None),
            limit=getattr(args, "limit", DEFAULT_LIMIT),
            receipt_path=receipt_path,
            state_path=state_path,
            mark_read=bool(getattr(args, "mark_read", False)),
            capture_receipt=bool(getattr(args, "capture_receipt", True)),
        )
    except BusInboxError as exc:
        print(f"bus_inbox: {exc}", file=sys.stderr)
        return 1

    try:
        channel_display = summary.channel_path.relative_to(ROOT)
    except ValueError:
        channel_display = summary.channel_path

    line = (
        f"Inbox agent-{summary.agent_id}: total={summary.total_messages} "
        f"new={summary.new_messages} last={summary.last_message_ts or '-'}"
    )
    print(line)
    if summary.receipt_path:
        try:
            receipt_display = summary.receipt_path.relative_to(ROOT)
        except ValueError:
            receipt_display = summary.receipt_path
        try:
            state_display = summary.state_path.relative_to(ROOT)
        except ValueError:
            state_display = summary.state_path
        print(f"  receipt={receipt_display} state={state_display} channel={channel_display}")
    else:
        print(f"  channel={channel_display}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_cli(args)


if __name__ == "__main__":
    raise SystemExit(main())
