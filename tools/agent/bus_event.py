#!/usr/bin/env python3
"""Append events to the agent coordination bus."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
EVENT_LOG = ROOT / "_bus" / "events" / "events.jsonl"
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"
CLAIMS_DIR = ROOT / "_bus" / "claims"
AGENT_REPORT_DIR = ROOT / "_report" / "agent"


TERMINAL_CLAIM_STATUSES = {"done", "released", "closed", "cancelled", "abandoned"}


REQUIRED_FIELDS = {"ts", "agent_id", "event", "summary"}
SEVERITY_LEVELS = {"low", "medium", "high"}


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


def _record_guard_failure(
    *,
    agent_id: str,
    task_id: str | None,
    event: str,
    reason: str,
    claim_owner: str | None,
    claim_status: str | None,
) -> None:
    report_dir = AGENT_REPORT_DIR / agent_id
    report_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "ts": _iso_now(),
        "agent_id": agent_id,
        "event": event,
        "reason": reason,
    }
    if task_id:
        payload["task_id"] = task_id
    if claim_owner is not None:
        payload["claim_owner"] = claim_owner
    if claim_status is not None:
        payload["claim_status"] = claim_status
    with (report_dir / "errors.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def _load_claim(task_id: str) -> dict[str, Any] | None:
    path = CLAIMS_DIR / f"{task_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid claim JSON in {path}: {exc}") from exc
    return data


def _ensure_claim_owner(agent_id: str, task_id: str, event: str) -> None:
    claim = _load_claim(task_id)
    if claim is None:
        reason = (
            f"task {task_id} has no claim file; run `python -m tools.agent.bus_claim claim --task {task_id}` first"
        )
        _record_guard_failure(
            agent_id=agent_id,
            task_id=task_id,
            event=event,
            reason=reason,
            claim_owner=None,
            claim_status=None,
        )
        raise SystemExit(reason)
    owner = str(claim.get("agent_id", "")).strip()
    status = str(claim.get("status", "")).strip().lower()
    if status in TERMINAL_CLAIM_STATUSES:
        return
    if owner != agent_id:
        reason = (
            f"task {task_id} currently claimed by {owner or 'UNKNOWN'} (status={status or 'active'}); "
            f"run bus_claim release/claim before logging {event}"
        )
        _record_guard_failure(
            agent_id=agent_id,
            task_id=task_id,
            event=event,
            reason=reason,
            claim_owner=owner or None,
            claim_status=status or None,
        )
        raise SystemExit(reason)


def _parse_kv_pairs(pairs: list[str] | None, *, context: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    if not pairs:
        return data
    for item in pairs:
        key, sep, value = item.partition("=")
        if not sep:
            raise SystemExit(f"invalid {context} field '{item}', expected key=value")
        data[key] = value
    return data


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
    extra_fields = _parse_kv_pairs(args.extra, context="extra")
    payload.update(extra_fields)
    if args.severity:
        severity = args.severity.strip().lower()
        if severity not in SEVERITY_LEVELS:
            allowed = ", ".join(sorted(SEVERITY_LEVELS))
            raise SystemExit(f"severity must be one of: {allowed}")
        payload["severity"] = severity

    guarded_events = {"status", "complete", "proposal", "pr_opened", "audit", "release"}
    if args.task and args.event in guarded_events:
        _ensure_claim_owner(agent_id, args.task, args.event)

    if args.consensus_decision:
        from tools.consensus import receipts as consensus_receipts

        meta = {
            "task_id": args.task or "",
            "plan_id": args.plan or "",
            "event": args.event,
        }
        meta.update(_parse_kv_pairs(args.consensus_meta, context="consensus meta"))
        existing_receipts = payload.get("receipts", []) or []
        output_path = None
        if args.consensus_output:
            output_path = Path(args.consensus_output)
        receipt_file = consensus_receipts.append_receipt(
            decision_id=args.consensus_decision,
            summary=args.summary,
            agent_id=agent_id,
            event=args.event,
            receipts=existing_receipts,
            metadata=meta,
            output=output_path,
        )
        rel_path = receipt_file.relative_to(ROOT)
        payload.setdefault("receipts", []).append(str(rel_path))

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
    log.add_argument(
        "--consensus-decision",
        help="Append a consensus receipt for the specified decision id",
    )
    log.add_argument(
        "--consensus-output",
        help="Override consensus receipt filename (relative to _report/consensus/)",
    )
    log.add_argument(
        "--consensus-meta",
        nargs="*",
        help="Additional key=value metadata for the consensus receipt",
    )
    log.add_argument(
        "--severity",
        help="Severity level (low|medium|high)",
    )
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
