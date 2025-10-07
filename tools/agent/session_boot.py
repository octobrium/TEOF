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
import contextlib
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EVENT_LOG = ROOT / "_bus" / "events" / "events.jsonl"
CLAIMS_DIR = ROOT / "_bus" / "claims"
MANAGER_REPORT_LOG = ROOT / "_bus" / "messages" / "manager-report.jsonl"
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"
SESSION_GUARD_DIR = ROOT / "_report" / "agent"
CONFIDENCE_ROOT = ROOT / "_report" / "agent"

from tools.agent import bus_status, session_sync, coord_dashboard


def _sanitize_iso_for_filename(ts: str) -> str:
    return ts.replace(":", "").replace("-", "")


def _relative_to_root(path: Path) -> Path | str:
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path


def _write_dirty_receipt(agent_id: str, status_output: str) -> Path:
    timestamp = _iso_now()
    receipt_dir = ROOT / "_report" / "session" / agent_id / "dirty-handoff"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    safe_ts = _sanitize_iso_for_filename(timestamp)
    receipt_path = receipt_dir / f"dirty-{safe_ts}.txt"
    header = (
        "# dirty handoff\n"
        f"# agent={agent_id}\n"
        f"# captured_at={timestamp}\n"
        "# git_status=git status --porcelain\n\n"
    )
    body = status_output.rstrip() + "\n" if status_output.strip() else "(no status output captured)\n"
    receipt_path.write_text(header + body, encoding="utf-8")
    return receipt_path


def _record_dirty_event(agent_id: str, receipt_path: Path) -> None:
    payload = {
        "ts": _iso_now(),
        "agent_id": agent_id,
        "event": "observation",
        "summary": "Dirty working tree detected during session_boot",
        "receipts": [str(_relative_to_root(receipt_path))],
    }
    _append_event(payload)


def _record_confidence(agent_id: str, confidence: float, note: str | None = None) -> Path:
    log_dir = CONFIDENCE_ROOT / agent_id
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "confidence.jsonl"
    payload: dict[str, Any] = {
        "ts": _iso_now(),
        "agent": agent_id,
        "confidence": confidence,
    }
    if note:
        payload["note"] = note
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")
    return log_path


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


class ManifestMismatchError(RuntimeError):
    """Raised when AGENT_MANIFEST.json does not match the requested agent."""


class BranchMismatchError(RuntimeError):
    """Raised when the git branch does not align with agent naming conventions."""


def _log_session_warning(agent_id: str, code: str, message: str, *, details: dict[str, Any] | None = None) -> None:
    warn_dir = SESSION_GUARD_DIR / agent_id / "session_guard"
    warn_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "ts": _iso_now(),
        "agent_id": agent_id,
        "code": code,
        "message": message,
    }
    if details:
        payload.update(details)
    warnings_path = warn_dir / "warnings.jsonl"
    with warnings_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def _get_current_branch() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        raise BranchMismatchError("Unable to determine current branch (run inside a git repository)")
    return result.stdout.strip()


def _ensure_manifest_agent(agent_id: str, *, allow_override: bool) -> None:
    manifest_agent = _default_agent()
    if not manifest_agent:
        return
    if manifest_agent == agent_id:
        return
    message = (
        f"Manifest agent mismatch: AGENT_MANIFEST.json declares '{manifest_agent}' but session_boot "
        f"was asked to operate as '{agent_id}'. Run `python -m tools.agent.manifest_helper activate {agent_id}` "
        "before starting the session, or pass --allow-manifest-mismatch if this is intentional."
    )
    if allow_override:
        _log_session_warning(
            agent_id,
            code="manifest_mismatch",
            message=message,
            details={"manifest_agent": manifest_agent},
        )
        print(f"Warning: {message}", file=sys.stderr)
        return
    raise ManifestMismatchError(message)


def _ensure_branch(agent_id: str, *, allow_override: bool) -> None:
    try:
        branch = _get_current_branch()
    except BranchMismatchError as exc:
        if allow_override:
            _log_session_warning(agent_id, code="branch_unknown", message=str(exc))
            print(f"Warning: {exc}", file=sys.stderr)
            return
        raise

    allowed_branch_prefix = f"agent/{agent_id}"
    allowed_exact = {"main", "origin/main"}

    matches = branch == allowed_branch_prefix or branch.startswith(f"{allowed_branch_prefix}/")
    matches = matches or branch in allowed_exact

    if matches:
        return

    message = (
        f"Branch mismatch: current branch '{branch}' does not start with '{allowed_branch_prefix}/'. "
        "Checkout or create an agent-specific branch before running session_boot, or pass --allow-branch-mismatch."
    )
    if allow_override:
        _log_session_warning(
            agent_id,
            code="branch_mismatch",
            message=message,
            details={"branch": branch},
        )
        print(f"Warning: {message}", file=sys.stderr)
        return
    raise BranchMismatchError(message)


def _tail_manager_report(agent_id: str, limit: int) -> tuple[Path, int]:
    """Capture the most recent manager-report entries for receipts."""

    if limit <= 0:
        limit = 10

    lines: list[str] = []
    if MANAGER_REPORT_LOG.exists():
        with MANAGER_REPORT_LOG.open("r", encoding="utf-8", errors="ignore") as handle:
            lines = handle.readlines()
    tail = lines[-limit:] if limit and len(lines) > limit else lines

    receipt_dir = ROOT / "_report" / "session" / agent_id
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = receipt_dir / "manager-report-tail.txt"

    captured_at = _iso_now()
    with receipt_path.open("w", encoding="utf-8") as handle:
        handle.write(
            "# manager-report tail\n"
            f"# source={MANAGER_REPORT_LOG.relative_to(ROOT).as_posix()}\n"
            f"# captured_at={captured_at}\n"
            f"# requested_entries={limit}\n"
            f"# written_entries={len(tail)}\n\n"
        )
        if tail:
            handle.writelines(tail)
        else:
            handle.write("(manager-report log missing or empty)\n")

    return receipt_path, len(tail)


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
    parser.add_argument(
        "--manager-report-tail",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Capture the latest manager-report entries for this session (default: enabled)",
    )
    parser.add_argument(
        "--manager-report-tail-count",
        type=int,
        default=10,
        help="How many manager-report entries to capture for the receipt (default: 10)",
    )
    parser.add_argument(
        "--allow-manifest-mismatch",
        action="store_true",
        help="Allow running even if AGENT_MANIFEST.json does not match the requested agent",
    )
    parser.add_argument(
        "--allow-branch-mismatch",
        action="store_true",
        help="Allow running even if the current git branch does not match agent/<id> conventions",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        help="Optional subjective confidence (0.0-1.0) to log alongside the session",
    )
    parser.add_argument(
        "--confidence-note",
        help="Optional note associated with --confidence",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    agent_id = args.agent or _default_agent()
    if not agent_id:
        parser.error("Agent id missing; provide --agent or populate AGENT_MANIFEST.json")

    if args.confidence is not None and not 0.0 <= args.confidence <= 1.0:
        parser.error("--confidence must be between 0.0 and 1.0")
    if args.confidence_note and args.confidence is None:
        parser.error("--confidence-note requires --confidence")

    printed_messages: list[str] = []

    try:
        _ensure_manifest_agent(agent_id, allow_override=args.allow_manifest_mismatch)
        _ensure_branch(agent_id, allow_override=args.allow_branch_mismatch)
    except ManifestMismatchError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except BranchMismatchError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.sync:
        try:
            sync_result = session_sync.run_sync(allow_dirty=args.sync_allow_dirty)
        except session_sync.DirtyWorktreeError as exc:
            receipt_path = _write_dirty_receipt(agent_id, exc.status_output)
            _record_dirty_event(agent_id, receipt_path)
            rel_receipt = _relative_to_root(receipt_path)
            print(
                "Session sync aborted: working tree has local changes; commit/stash or rerun with --sync-allow-dirty.",
                file=sys.stderr,
            )
            for line in exc.status_output.splitlines():
                print(f"  {line}", file=sys.stderr)
            print(f"  receipt={rel_receipt}", file=sys.stderr)
            print(
                "  observation logged to _bus/events/events.jsonl; follow up with bus_event status if coordination needs more detail.",
                file=sys.stderr,
            )
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

    printed_messages.append(
        "Tip: keep the manager-report feed open with `python -m tools.agent.bus_watch --task manager-report --follow --limit 20`"
    )

    if args.confidence is not None:
        confidence_path = _record_confidence(agent_id, args.confidence, args.confidence_note)
        rel_conf_path = _relative_to_root(confidence_path)
        printed_messages.append(
            f"Confidence logged ({args.confidence:.2f}) → {rel_conf_path}"
        )

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

    if args.manager_report_tail:
        receipt_path, written = _tail_manager_report(agent_id, args.manager_report_tail_count)
        printed_messages.append("manager-report tail captured")
        try:
            rel_receipt = receipt_path.relative_to(ROOT)
        except ValueError:
            rel_receipt = receipt_path
        printed_messages.append(f"  entries={written} receipt={rel_receipt}")
    else:
        printed_messages.append("manager-report tail capture skipped (--no-manager-report-tail)")

    for message in printed_messages:
        print(message)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
