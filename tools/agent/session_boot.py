#!/usr/bin/env python3
"""Session bootstrap helper for agents.

Logs a handshake event on the coordination bus and reports other active agents
and their claimed tasks so operators can coordinate without manual back-and-forth.
Runs a repository sync (`git fetch --prune && git pull --ff-only`) before the
handshake by default so each session starts from the latest commit. Can
optionally run `bus_status` immediately after the handshake to capture a
current snapshot for receipts.
"""
from __future__ import annotations

import argparse
import json
import contextlib
import sys
from io import StringIO
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EVENT_LOG = ROOT / "_bus" / "events" / "events.jsonl"
CLAIMS_DIR = ROOT / "_bus" / "claims"
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"

from tools.agent import bus_status, session_sync, coord_dashboard


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
        "--sync",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run git fetch/pull before logging the handshake (default: enabled)",
    )
    parser.add_argument(
        "--sync-allow-dirty",
        action="store_true",
        help="Allow sync to proceed even with local changes present",
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
    parser.add_argument(
        "--dashboard",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run coord_dashboard after the handshake (default: enabled)",
    )
    parser.add_argument(
        "--dashboard-format",
        choices=["json", "markdown"],
        default="json",
        help="Format to capture when running coord_dashboard (default: json)",
    )
    parser.add_argument(
        "--dashboard-receipt",
        help="Optional path for the coord_dashboard receipt (defaults under _report/agent/<id>/session_boot/)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    agent_id = args.agent or _default_agent()
    if not agent_id:
        parser.error("Agent id missing; provide --agent or populate AGENT_MANIFEST.json")

    printed_messages: list[str] = []

    if args.sync:
        try:
            sync_result = session_sync.run_sync(allow_dirty=args.sync_allow_dirty)
        except session_sync.DirtyWorktreeError as exc:
            print(
                "Session sync aborted: working tree has local changes; commit/stash or rerun with --sync-allow-dirty.",
                file=sys.stderr,
            )
            for line in exc.status_output.splitlines():
                print(f"  {line}", file=sys.stderr)
            return 1
        except session_sync.SessionSyncError as exc:
            print(f"Session sync failed: {exc}", file=sys.stderr)
            return 1
        else:
            summary = "updates applied" if sync_result.changed else "repository already up to date"
            if sync_result.dirty:
                summary = f"{summary}, local changes retained"
            printed_messages.append(f"Session sync: {summary}")
    else:
        printed_messages.append("Session sync skipped (--no-sync)")

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

    if args.dashboard:
        dash_receipt = Path(args.dashboard_receipt) if args.dashboard_receipt else None
        if dash_receipt is None:
            suffix = "md" if args.dashboard_format == "markdown" else "json"
            dash_receipt = (
                ROOT
                / "_report"
                / "agent"
                / agent_id
                / "session_boot"
                / f"coordination-dashboard-{_iso_now()}.{suffix}"
            )
        dash_receipt.parent.mkdir(parents=True, exist_ok=True)
        dash_buffer = StringIO()
        try:
            coord_dashboard.run_report(
                root=ROOT,
                fmt=args.dashboard_format,
                manager_window=coord_dashboard.DEFAULT_MANAGER_WINDOW_MINUTES,
                agent_window=coord_dashboard.DEFAULT_AGENT_WINDOW_MINUTES,
                directive_limit=coord_dashboard.DEFAULT_DIRECTIVE_LIMIT,
                output_path=dash_receipt,
                compact=False,
                stream=dash_buffer,
            )
        except coord_dashboard.DashboardError as exc:
            print(f"coord_dashboard failed: {exc}", file=sys.stderr)
            return 1
        printed_messages.append(
            "coord_dashboard snapshot captured"
        )
        try:
            rel_receipt = dash_receipt.relative_to(ROOT)
        except ValueError:
            rel_receipt = dash_receipt
        printed_messages.append(f"  receipt={rel_receipt}")
    else:
        printed_messages.append("coord_dashboard skipped (--no-dashboard)")

    for message in printed_messages:
        print(message)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
