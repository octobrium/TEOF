#!/usr/bin/env python3
"""Orchestrate the standard TEOF agent lane (handshake → claim → broadcast)."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

from teof._paths import repo_root
from tools.agent import bus_claim, bus_ping, session_boot


ROOT = repo_root(default=Path(__file__).resolve().parents[2])


def _timestamp() -> str:
    return dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def _write_receipt(agent_id: str, payload: dict[str, Any]) -> Path:
    lane_dir = ROOT / "_report" / "agent" / agent_id / "lane"
    lane_dir.mkdir(parents=True, exist_ok=True)
    ts = payload["ts"]
    path = lane_dir / f"lane-{ts}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _run_step(label: str, func, argv: list[str], actions: list[dict[str, Any]]) -> None:
    exit_code = func(argv)
    actions.append(
        {
            "step": label,
            "argv": argv,
            "exit_code": exit_code,
        }
    )
    if exit_code != 0:
        raise RuntimeError(f"{label} failed with exit code {exit_code}")


def _build_handshake_args(args: argparse.Namespace) -> list[str]:
    argv = ["--agent", args.agent]
    if args.focus:
        argv += ["--focus", args.focus]
    if args.handshake_summary:
        argv += ["--summary", args.handshake_summary]
    if args.handshake_with_status:
        argv.append("--with-status")
    if args.handshake_receipt:
        argv += ["--receipt", args.handshake_receipt]
    if not args.handshake_sync:
        argv.append("--no-sync")
    if not args.handshake_dashboard:
        argv.append("--no-dashboard")
    if not args.handshake_manager_tail:
        argv.append("--no-manager-report-tail")
    if args.allow_manifest_mismatch:
        argv.append("--allow-manifest-mismatch")
    if args.allow_branch_mismatch:
        argv.append("--allow-branch-mismatch")
    return argv


def _build_claim_args(args: argparse.Namespace) -> list[str]:
    argv = [
        "claim",
        "--task",
        args.task,
        "--agent",
        args.agent,
        "--status",
        args.claim_status,
    ]
    if args.plan:
        argv += ["--plan", args.plan]
    if args.branch:
        argv += ["--branch", args.branch]
    if args.claim_notes:
        argv += ["--notes", args.claim_notes]
    if args.allow_unassigned:
        argv.append("--allow-unassigned")
    if args.claim_allow_stale_session:
        argv.append("--allow-stale-session")
    if args.claim_session_max_age is not None:
        argv += ["--session-max-age", str(args.claim_session_max_age)]
    return argv


def _build_ping_args(args: argparse.Namespace) -> list[str]:
    summary = args.summary or "lane heartbeat"
    argv: list[str] = [
        "--summary",
        summary,
        "--event",
        args.event,
        "--agent",
        args.agent,
    ]
    if args.task:
        argv += ["--task", args.task]
    if args.plan:
        argv += ["--plan", args.plan]
    if args.branch:
        argv += ["--branch", args.branch]
    if args.pr:
        argv += ["--pr", args.pr]
    if args.event_receipt:
        argv += ["--event-receipt", args.event_receipt]
    if args.message_task:
        argv += ["--message-task", args.message_task]
    if args.message_type:
        argv += ["--message-type", args.message_type]
    if args.note:
        argv += ["--note", args.note]
    for receipt in args.message_receipt or []:
        argv += ["--message-receipt", receipt]
    for meta in args.message_meta or []:
        argv += ["--message-meta", meta]
    if args.skip_message:
        argv.append("--skip-message")
    if args.allow_stale_session:
        argv.append("--allow-stale-session")
    if args.session_max_age is not None:
        argv += ["--session-max-age", str(args.session_max_age)]
    return argv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stand up the standard TEOF agent lane (handshake, claim, broadcast)"
    )
    parser.add_argument("--agent", required=True, help="Agent id to operate as")
    parser.add_argument("--focus", help="Focus string recorded during the handshake")
    parser.add_argument("--task", help="Task identifier (e.g., QUEUE-001)")
    parser.add_argument("--plan", help="Plan identifier to associate with the claim + heartbeat")
    parser.add_argument("--branch", help="Branch name to record in the claim/heartbeat")
    parser.add_argument("--summary", help="Heartbeat summary (defaults to 'lane heartbeat')")
    parser.add_argument("--event", default="status", help="bus_event type (default: status)")
    parser.add_argument("--pr", help="Related PR identifier for the heartbeat")
    parser.add_argument("--note", help="Optional note for the bus message")
    parser.add_argument("--message-task", help="If set, also post to _bus/messages/<task>.jsonl")
    parser.add_argument("--message-type", default="status", help="bus_message type (default: status)")
    parser.add_argument("--message-receipt", action="append", help="Receipt path(s) to attach to the bus message")
    parser.add_argument("--message-meta", action="append", help="Additional key=value metadata for the bus message")
    parser.add_argument("--event-receipt", help="Receipt path to attach to the bus event")

    # Handshake toggles
    parser.add_argument("--skip-handshake", action="store_true", help="Skip session_boot")
    parser.add_argument("--handshake-summary", help="Override the handshake summary text")
    parser.add_argument(
        "--handshake-with-status",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run bus_status inside session_boot (default: enabled)",
    )
    parser.add_argument("--handshake-receipt", help="Optional path for the bus_status receipt")
    parser.add_argument(
        "--handshake-sync",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run git sync inside session_boot (default: enabled)",
    )
    parser.add_argument(
        "--handshake-dashboard",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Capture coord_dashboard during session_boot (default: enabled)",
    )
    parser.add_argument(
        "--handshake-manager-tail",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Capture manager-report tail during session_boot (default: enabled)",
    )
    parser.add_argument(
        "--allow-manifest-mismatch",
        action="store_true",
        help="Allow running even if AGENT_MANIFEST does not match the seat",
    )
    parser.add_argument(
        "--allow-branch-mismatch",
        action="store_true",
        help="Allow running even if the git branch does not match agent/<id>",
    )

    # Claim toggles
    parser.add_argument("--skip-claim", action="store_true", help="Skip bus_claim (default: run if --task is set)")
    parser.add_argument("--claim-status", default="active", help="Claim status (default: active)")
    parser.add_argument("--claim-notes", help="Notes to attach to the claim")
    parser.add_argument("--allow-unassigned", action="store_true", help="Bypass assignment requirement when claiming")
    parser.add_argument(
        "--claim-allow-stale-session",
        action="store_true",
        help="Allow stale sessions when claiming (not recommended)",
    )
    parser.add_argument(
        "--claim-session-max-age",
        type=int,
        help="Override session freshness check (seconds) for the claim helper",
    )

    # Broadcast toggles
    parser.add_argument("--skip-event", action="store_true", help="Skip the bus_ping heartbeat stage")
    parser.add_argument("--skip-message", action="store_true", help="Skip the optional bus_message (even if set)")
    parser.add_argument(
        "--allow-stale-session",
        action="store_true",
        help="Allow stale sessions when emitting the heartbeat (not recommended)",
    )
    parser.add_argument(
        "--session-max-age",
        type=int,
        help="Override session freshness (seconds) enforced by bus_ping",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.task and not args.skip_claim:
        parser.error("--task is required unless --skip-claim is supplied")

    actions: list[dict[str, Any]] = []
    ts = _timestamp()
    status = "ok"
    error: str | None = None

    try:
        if not args.skip_handshake:
            handshake_argv = _build_handshake_args(args)
            _run_step("session_boot", session_boot.main, handshake_argv, actions)

        if args.task and not args.skip_claim:
            claim_argv = _build_claim_args(args)
            _run_step("bus_claim", bus_claim.main, claim_argv, actions)

        if not args.skip_event:
            ping_argv = _build_ping_args(args)
            _run_step("bus_ping", bus_ping.main, ping_argv, actions)

    except RuntimeError as exc:
        status = "error"
        error = str(exc)
        print(error)

    payload = {
        "ts": ts,
        "agent": args.agent,
        "task": args.task,
        "plan": args.plan,
        "branch": args.branch,
        "status": status,
        "summary": args.summary or "lane heartbeat",
        "actions": actions,
    }
    if error:
        payload["error"] = error

    receipt_path = _write_receipt(args.agent, payload)
    rel_path = receipt_path.relative_to(ROOT)
    if status == "ok":
        print(f"lane: recorded handshake/claim/broadcast receipt → {rel_path}")
        return 0
    print(f"lane: recorded failure receipt → {rel_path}")
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
