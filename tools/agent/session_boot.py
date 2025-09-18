#!/usr/bin/env python3
"""Session bootstrap helper for agents.

Logs a handshake event on the coordination bus and reports other active agents
and their claimed tasks so operators can coordinate without manual back-and-forth.
Can optionally run `bus_status` immediately after the handshake to capture a
current snapshot for receipts.
"""
from __future__ import annotations

import argparse
import json
import contextlib
from io import StringIO
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EVENT_LOG = ROOT / "_bus" / "events" / "events.jsonl"
CLAIMS_DIR = ROOT / "_bus" / "claims"
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"

from tools.agent import bus_status


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


def _load_claims() -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    if not CLAIMS_DIR.exists():
        return claims
    for path in sorted(CLAIMS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        data["_path"] = path.relative_to(ROOT).as_posix()
        claims.append(data)
    return claims


def summarize_peers(claims: list[dict[str, Any]], self_agent: str) -> list[str]:
    peers: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for claim in claims:
        agent_id = claim.get("agent_id")
        status = claim.get("status")
        if agent_id and agent_id != self_agent and status in {"active", "paused"}:
            peers[agent_id].append(claim)
    summary: list[str] = []
    for agent_id, rows in sorted(peers.items()):
        tasks = ", ".join(f"{row.get('task_id')}[{row.get('status')}]=@{row.get('branch')}" for row in rows)
        summary.append(f"Peer {agent_id}: {tasks}")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap an agent session")
    parser.add_argument("--agent", help="Agent id (defaults to AGENT_MANIFEST.json)")
    parser.add_argument("--summary", default="Session handshake", help="Summary text for the handshake event")
    parser.add_argument("--focus", help="Focus area recorded in handshake metadata")
    parser.add_argument(
        "--no-announce",
        action="store_true",
        help="Skip logging the handshake event (useful for dry runs)",
    )
    parser.add_argument(
        "--with-status",
        action="store_true",
        help="Run bus_status after the handshake to capture a quick summary",
    )
    parser.add_argument(
        "--status-preset",
        choices=sorted(bus_status.PRESETS.keys()),
        default="support",
        help="Preset to use when running bus_status (default: support)",
    )
    parser.add_argument(
        "--status-agent",
        help="Agent id to filter when running bus_status (defaults to this agent)",
    )
    parser.add_argument(
        "--receipt",
        help="When provided, write the bus_status output to this path",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    agent_id = args.agent or _default_agent()
    if not agent_id:
        parser.error("Agent id missing; provide --agent or populate AGENT_MANIFEST.json")

    printed_messages: list[str] = []

    if not args.no_announce:
        payload = {
            "ts": _iso_now(),
            "agent_id": agent_id,
            "event": "handshake",
            "summary": args.summary,
            "branch_prefix": f"agent/{agent_id}/",
        }
        if args.focus:
            payload["meta"] = {"focus": args.focus}
        _append_event(payload)
        printed_messages.append(f"Recorded handshake for {agent_id} at {payload['ts']}")
        if args.focus:
            printed_messages.append(f"Focus: {args.focus}")
    else:
        printed_messages.append("Handshake skipped (--no-announce)")

    claims = _load_claims()
    summary_lines = summarize_peers(claims, agent_id)

    if summary_lines:
        printed_messages.append("Other active agents detected:")
        for line in summary_lines:
            printed_messages.append(f"  - {line}")
    else:
        printed_messages.append("No other active agents detected.")

    status_output = ""
    if args.with_status:
        status_args = ["--summary", "--preset", args.status_preset]
        status_agent = args.status_agent or agent_id
        if status_agent:
            status_args.extend(["--agent", status_agent])
        buf = StringIO()
        with contextlib.redirect_stdout(buf):
            exit_code = bus_status.main(status_args)
        status_output = buf.getvalue()
        if exit_code != 0:
            print(status_output, end="")
            return exit_code
        printed_messages.append("bus_status summary:")
        printed_messages.extend([f"  {line}" for line in status_output.strip().splitlines() if line.strip()])
        if args.receipt:
            receipt_path = Path(args.receipt)
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(status_output, encoding="utf-8")

    for message in printed_messages:
        print(message)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
