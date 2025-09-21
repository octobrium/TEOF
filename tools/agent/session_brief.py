#!/usr/bin/env python3
"""Summarize claim + coordination history for a task (and emit presets)."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional, Sequence

ROOT = Path(__file__).resolve().parents[2]
CLAIMS_DIR = ROOT / "_bus" / "claims"
EVENT_LOG = ROOT / "_bus" / "events" / "events.jsonl"
MESSAGES_DIR = ROOT / "_bus" / "messages"
SESSION_DIR = ROOT / "_report" / "session"
PLANNER_VALIDATE_DIR = ROOT / "_report" / "planner" / "validate"
SESSION_BRIEF_DIR = ROOT / "_report" / "agent"
USAGE_REPORT_DIR = ROOT / "_report" / "usage"
QUICKSTART_LATEST = ROOT / "artifacts" / "ocers_out" / "latest"
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
TERMINAL_CLAIM_STATUSES = {"done", "released", "closed", "cancelled", "abandoned"}


def parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.strptime(ts, ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def load_claim(task: str) -> dict | None:
    path = CLAIMS_DIR / f"{task}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise SystemExit(f"invalid JSON in {path}")


def summarize_claim(claim: dict | None, task: str) -> str:
    if not claim:
        return f"No claim found for {task}."
    parts = [
        f"Task: {task}",
        f"Agent: {claim.get('agent_id', '-')}",
        f"Status: {claim.get('status', '-')}",
    ]
    if claim.get("plan_id"):
        parts.append(f"Plan: {claim['plan_id']}")
    if claim.get("branch"):
        parts.append(f"Branch: {claim['branch']}")
    if claim.get("claimed_at"):
        parts.append(f"Claimed at: {claim['claimed_at']}")
    if claim.get("notes"):
        parts.append(f"Notes: {claim['notes']}")
    return " | ".join(parts)


def format_entries(entries: Iterable[dict], *, limit: int, title: str) -> str:
    selected = sorted(
        (entry for entry in entries if entry),
        key=lambda e: parse_iso(e.get("ts")) or datetime.min,
        reverse=True,
    )[:limit]
    if not selected:
        return f"{title}: none"
    lines = [f"{title} (latest {len(selected)}):"]
    for entry in selected:
        ts = entry.get("ts", "?")
        agent = entry.get("agent_id") or entry.get("from") or "?"
        kind = entry.get("event") or entry.get("type") or ""
        summary = entry.get("summary", "")
        plan = entry.get("plan_id")
        extra = f" plan={plan}" if plan else ""
        kind_part = f" [{kind}]" if kind else ""
        lines.append(f"  - {ts} :: {agent}{extra}{kind_part} :: {summary}")
    return "\n".join(lines)


def _relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _load_manifest_agent() -> Optional[str]:
    if not MANIFEST_PATH.exists():
        return None
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    agent = data.get("agent_id")
    return str(agent).strip() if isinstance(agent, str) and agent.strip() else None


def _resolve_agent_id(explicit: Optional[str], claim: dict | None) -> Optional[str]:
    if explicit:
        return explicit.strip()
    if claim:
        candidate = claim.get("agent_id")
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return _load_manifest_agent()


def _check_manager_tail(agent_id: Optional[str]) -> dict:
    if not agent_id:
        return {
            "id": "manager_tail",
            "title": "Manager-report tail receipt",
            "status": "fail",
            "detail": "Agent id unknown; cannot locate _report/session/<agent>/manager-report-tail.txt",
            "paths": [],
        }
    path = SESSION_DIR / agent_id / "manager-report-tail.txt"
    if path.exists():
        return {
            "id": "manager_tail",
            "title": "Manager-report tail receipt",
            "status": "pass",
            "detail": "Manager-report tail receipt present",
            "paths": [_relative(path)],
        }
    return {
        "id": "manager_tail",
        "title": "Manager-report tail receipt",
        "status": "fail",
        "detail": "Missing _report/session/<agent>/manager-report-tail.txt",
        "paths": [_relative(path)],
    }


def _latest_planner_summary() -> Optional[Path]:
    if not PLANNER_VALIDATE_DIR.exists():
        return None
    summaries = sorted(PLANNER_VALIDATE_DIR.glob("summary-*.json"))
    return summaries[-1] if summaries else None


def _check_planner_validation() -> dict:
    summary = _latest_planner_summary()
    if summary:
        return {
            "id": "planner_validate",
            "title": "Strict plan validation",
            "status": "pass",
            "detail": "Plan validation summary found",
            "paths": [_relative(summary)],
        }
    return {
        "id": "planner_validate",
        "title": "Strict plan validation",
        "status": "warn",
        "detail": "No planner validation summary located under _report/planner/validate/",
        "paths": [_relative(PLANNER_VALIDATE_DIR)],
    }


def _check_quickstart_receipts() -> dict:
    brief_path = QUICKSTART_LATEST / "brief.json"
    if brief_path.exists():
        return {
            "id": "quickstart_receipts",
            "title": "Quickstart receipts present",
            "status": "pass",
            "detail": "Found artifacts/ocers_out/latest/brief.json",
            "paths": [_relative(brief_path)],
        }
    return {
        "id": "quickstart_receipts",
        "title": "Quickstart receipts present",
        "status": "warn",
        "detail": "Quickstart artifacts missing; rerun docs/quickstart.md to refresh receipts",
        "paths": [_relative(brief_path)],
    }


def _check_claim_state(task: str, claim: dict | None) -> dict:
    if not claim:
        return {
            "id": "claim_seed",
            "title": "Claim seeded for task",
            "status": "fail",
            "detail": f"No claim found for {task}; run tools.agent.claim_seed before handoff",
            "paths": [_relative(CLAIMS_DIR)],
        }
    status = str(claim.get("status", "")).strip().lower()
    detail = f"Claim status={status or 'unknown'}"
    state = "pass"
    if status in TERMINAL_CLAIM_STATUSES:
        state = "warn"
        detail += " (terminal)"
    return {
        "id": "claim_seed",
        "title": "Claim seeded for task",
        "status": state,
        "detail": detail,
        "paths": [_relative(CLAIMS_DIR / f"{task}.json")],
    }


def _check_task_sync(agent_id: Optional[str]) -> dict:
    if not agent_id:
        return {
            "id": "task_sync",
            "title": "Task sync receipts",
            "status": "warn",
            "detail": "Agent id unknown; cannot verify task sync receipts",
            "paths": [],
        }
    sync_dir = SESSION_BRIEF_DIR / agent_id / "task_sync"
    if sync_dir.exists() and any(sync_dir.iterdir()):
        return {
            "id": "task_sync",
            "title": "Task sync receipts",
            "status": "pass",
            "detail": "Task sync receipts present",
            "paths": [_relative(sync_dir)],
        }
    return {
        "id": "task_sync",
        "title": "Task sync receipts",
        "status": "warn",
        "detail": "No task sync receipts detected; run python -m tools.agent.task_sync",
        "paths": [_relative(sync_dir)],
    }


def _check_receipts_index() -> dict:
    if not USAGE_REPORT_DIR.exists():
        return {
            "id": "receipts_index",
            "title": "Receipts index ledger",
            "status": "warn",
            "detail": "_report/usage/ missing receipts-index ledger; run tools.agent.receipts_index",
            "paths": [_relative(USAGE_REPORT_DIR)],
        }
    matches = sorted(p for p in USAGE_REPORT_DIR.glob("*receipts-index*.jsonl"))
    if matches:
        return {
            "id": "receipts_index",
            "title": "Receipts index ledger",
            "status": "pass",
            "detail": f"Found {len(matches)} receipts-index JSONL file(s)",
            "paths": [_relative(matches[-1])],
        }
    return {
        "id": "receipts_index",
        "title": "Receipts index ledger",
        "status": "warn",
        "detail": "No receipts-index JSONL located; run tools.agent.receipts_index",
        "paths": [_relative(USAGE_REPORT_DIR)],
    }


def _check_receipts_hygiene() -> dict:
    summary_path = USAGE_REPORT_DIR / "receipts-hygiene-summary.json"
    if not summary_path.exists():
        return {
            "id": "receipts_hygiene",
            "title": "Receipts hygiene summary",
            "status": "warn",
            "detail": "Missing receipts-hygiene-summary.json; run tools.agent.receipts_hygiene",
            "paths": [_relative(summary_path)],
        }
    try:
        data = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "id": "receipts_hygiene",
            "title": "Receipts hygiene summary",
            "status": "fail",
            "detail": "receipts-hygiene-summary.json is not valid JSON",
            "paths": [_relative(summary_path)],
        }

    metrics = data.get("metrics", {}) if isinstance(data, dict) else {}
    missing = metrics.get("plans_missing_receipts")
    slow_plans = metrics.get("slow_plans") if isinstance(metrics, dict) else None
    slow_count = len(slow_plans) if isinstance(slow_plans, list) else 0

    if isinstance(missing, (int, float)) and missing > 0:
        status = "warn"
        detail = f"{int(missing)} plan(s) missing receipts; escalate before continuing"
    else:
        status = "pass"
        detail = "Receipts hygiene summary present"
        if slow_count:
            detail += f"; {slow_count} slow plan(s) tracked"

    return {
        "id": "receipts_hygiene",
        "title": "Receipts hygiene summary",
        "status": status,
        "detail": detail,
        "paths": [_relative(summary_path)],
    }


def _operator_checklist(agent_id: Optional[str], task: str, claim: dict | None) -> list[dict]:
    return [
        _check_manager_tail(agent_id),
        _check_planner_validation(),
        _check_quickstart_receipts(),
        _check_claim_state(task, claim),
        _check_task_sync(agent_id),
        _check_receipts_index(),
        _check_receipts_hygiene(),
    ]


def _compute_summary(checks: Sequence[dict]) -> str:
    summary = "pass"
    for item in checks:
        status = item.get("status")
        if status == "fail":
            return "fail"
        if status == "warn" and summary == "pass":
            summary = "warn"
    return summary


def _write_operator_receipt(agent_id: Optional[str], report: dict, output: Optional[str]) -> Path:
    if output:
        path = Path(output)
        if not path.is_absolute():
            path = (ROOT / path).resolve()
    else:
        if agent_id:
            base = SESSION_BRIEF_DIR / agent_id / "session_brief"
        else:
            base = USAGE_REPORT_DIR
        base.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        path = base / f"session-brief-operator-{timestamp}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _run_operator_preset(agent_id: Optional[str], task: str, claim: dict | None, *, output: Optional[str]) -> dict:
    generated_at = datetime.utcnow().replace(tzinfo=timezone.utc).strftime(ISO_FMT)
    checks = _operator_checklist(agent_id, task, claim)
    summary = _compute_summary(checks)
    report = {
        "preset": "operator",
        "generated_at": generated_at,
        "agent_id": agent_id,
        "task": task,
        "claim_status": claim.get("status") if claim else None,
        "checklist": checks,
        "summary": summary,
    }
    receipt_path = _write_operator_receipt(agent_id, report, output)
    report["receipt_path"] = _relative(receipt_path)
    return report


def _print_operator_summary(report: dict) -> None:
    print("\nOperator preset summary:")
    for item in report.get("checklist", []):
        status = item.get("status", "?").upper()
        print(f"  [{status}] {item.get('title')} — {item.get('detail')}")
    receipt = report.get("receipt_path")
    if receipt:
        print(f"Operator preset receipt: {receipt}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Show claim + bus history for a task")
    parser.add_argument("--task", required=True, help="Task identifier (e.g., QUEUE-010)")
    parser.add_argument("--limit", type=int, default=5, help="Max events/messages to display")
    parser.add_argument("--preset", choices=["operator"], help="Run additional preset checks")
    parser.add_argument("--agent", help="Override agent id for presets")
    parser.add_argument("--output", help="Write preset output to custom JSON path")
    args = parser.parse_args(argv)

    task = args.task.upper()
    claim = load_claim(task)
    print(summarize_claim(claim, task))

    events = [
        entry
        for entry in load_jsonl(EVENT_LOG)
        if entry.get("task_id") == task
    ]
    print(format_entries(events, limit=args.limit, title="Events"))

    msg_path = MESSAGES_DIR / f"{task}.jsonl"
    messages = load_jsonl(msg_path)
    print(format_entries(messages, limit=args.limit, title="Messages"))

    if args.preset == "operator":
        agent_id = _resolve_agent_id(args.agent, claim)
        report = _run_operator_preset(agent_id, task, claim, output=args.output)
        _print_operator_summary(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
