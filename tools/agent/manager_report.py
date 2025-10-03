#!/usr/bin/env python3
"""Generate a manager summary of active tasks and receipts."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools import reconcile_metrics_summary as metrics_summary
from tools.planner import queue_warnings as planner_queue_warnings
from tools.planner.validate import validate_plan

ROOT = Path(__file__).resolve().parents[2]
ASSIGN_DIR = ROOT / "_bus" / "assignments"
CLAIMS_DIR = ROOT / "_bus" / "claims"
MESSAGES_DIR = ROOT / "_bus" / "messages"
REPORT_DIR = ROOT / "_report" / "manager"
TASKS_FILE = ROOT / "agents" / "tasks" / "tasks.json"
AUTH_JSON = ROOT / "_report" / "usage" / "external-authenticity.json"
AUTH_MD = ROOT / "_report" / "usage" / "external-authenticity.md"
PLANS_DIR = ROOT / "_plans"


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def load_tasks() -> list[dict[str, Any]]:
    data = load_json(TASKS_FILE)
    if isinstance(data, dict) and isinstance(data.get("tasks"), list):
        return data["tasks"]
    return []


def collect_claims() -> dict[str, Any]:
    info: dict[str, Any] = {}
    for path in sorted(CLAIMS_DIR.glob("*.json")):
        info[path.stem] = load_json(path)
    return info


def collect_assignments() -> dict[str, Any]:
    data: dict[str, Any] = {}
    for path in sorted(ASSIGN_DIR.glob("*.json")):
        data[path.stem] = load_json(path)
    return data


def summarize_messages(task_id: str) -> list[str]:
    path = MESSAGES_DIR / f"{task_id}.jsonl"
    if not path.exists():
        return []
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            continue
        ts = msg.get("ts")
        sender = msg.get("from")
        summary = msg.get("summary")
        lines.append(f"- {ts} :: {sender}: {summary}")
    return lines


def write_report(
    manager_id: str,
    tasks: list[dict[str, Any]],
    assignments: dict[str, Any],
    claims: dict[str, Any],
    metrics: dict[str, Any] | None,
    authenticity: dict[str, Any] | None,
    planner_warnings: list[dict[str, Any]] | None,
    plan_validation_issues: list[dict[str, Any]] | None = None,
) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = iso_now()
    report_path = REPORT_DIR / f"manager-report-{ts}.md"
    lines = [f"# Manager Report — {ts}", "", f"Manager: `{manager_id}`", ""]

    for task in tasks:
        task_id = task.get("id")
        lines.append(f"## {task_id} — {task.get('title')}")
        lines.append(f"- Role: {task.get('role', 'n/a')} | Priority: {task.get('priority', 'n/a')} | Status: {task.get('status', 'n/a')}")
        if task.get("plan_id"):
            lines.append(f"- Plan: `{task['plan_id']}`")
        if task.get("branch"):
            lines.append(f"- Branch: `{task['branch']}`")
        if task.get("receipts"):
            receipt_list = ', '.join(task.get("receipts", []))
            lines.append(f"- Receipts: {receipt_list}")
        assignment = assignments.get(task_id)
        if assignment:
            lines.append(f"- Assigned to `{assignment.get('engineer')}` at {assignment.get('assigned_at')} (note: {assignment.get('note')})")
        claim = claims.get(task_id)
        if claim:
            lines.append(f"- Current claim: {claim.get('agent_id')} [{claim.get('status')}] → {claim.get('branch')}")
        message_lines = summarize_messages(task_id)
        if message_lines:
            lines.append("- Messages:")
            lines.extend([f"  {msg}" for msg in message_lines])
        if task.get("notes"):
            lines.append(f"- Notes: {task['notes']}")
        lines.append("")

    if planner_warnings:
        lines.append("## Planner Queue Warnings")
        for warning in planner_warnings:
            if isinstance(warning, dict):
                message = warning.get("message", "(no message)")
                plan_id = warning.get("plan_id", "-")
                queue_ref = warning.get("queue_ref", "-")
                issue = warning.get("issue", "-")
                lines.append(
                    f"- {plan_id} [{issue}] ← {queue_ref}: {message}"
                )
            else:
                lines.append(f"- {warning}")
        lines.append("")

    if plan_validation_issues:
        lines.append("## Plan Validation Issues")
        for issue in plan_validation_issues:
            plan_path = issue.get("plan")
            errors = issue.get("errors", [])
            if plan_path:
                lines.append(f"- {plan_path}")
                prefix = "  - "
            else:
                prefix = "- "
            if errors:
                for err in errors:
                    lines.append(f"{prefix}{err}")
            else:
                lines.append(f"{prefix}(no details provided)")
        lines.append("")

    if metrics:
        match_ratio = metrics.get("match_ratio")
        ratio_str = f"{match_ratio:.2f}" if isinstance(match_ratio, (int, float)) and match_ratio is not None else "n/a"
        lines.append("## Reconciliation Metrics")
        lines.append(
            f"- Runs: {metrics['total_runs']} | Match ratio: {ratio_str}"
        )
        lines.append(
            f"- Differences: {metrics['difference_total']} | Missing receipts: {metrics['missing_receipt_total']} | Capability diffs: {metrics['capability_diff_total']}"
        )
        files_scanned = metrics.get("files_scanned")
        if files_scanned is not None:
            lines.append(f"- Metrics files scanned: {files_scanned}")
        lines.append("")

    if authenticity:
        lines.append("## External Authenticity")
        overall = authenticity.get("overall_avg_trust")
        overall_str = "n/a" if overall is None else f"{overall:.3f}"
        lines.append(f"- Overall adjusted trust: {overall_str}")
        tier_entries = authenticity.get("tiers", [])
        for tier in tier_entries:
            tier_name = tier.get("tier")
            avg = tier.get("avg_adjusted_trust")
            avg_str = "n/a" if avg is None else f"{avg:.3f}"
            lines.append(
                f"  - {tier_name}: feeds={tier.get('feed_count')} | weight={tier.get('weight')} | avg={avg_str}"
            )
        attention = authenticity.get("attention_feeds", [])
        if attention:
            lines.append("- Attention feeds:")
            for feed in attention[:5]:
                lines.append(
                    f"  - {feed.get('feed_id')} ({feed.get('tier')}) — status={feed.get('status')} trust={feed.get('trust_adjusted')}"
                )
        if AUTH_MD.exists():
            lines.append(f"- Dashboard: `{AUTH_MD}`")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def _parse_meta(pairs: list[str]) -> list[str]:
    extras: list[str] = []
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"heartbeat meta must be key=value (got: {pair})")
        key, value = pair.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError("heartbeat meta key must be non-empty")
        extras.append(f"{key}={value.strip()}")
    return extras


def log_heartbeat(manager_id: str, summary: str, *, extras: list[str] | None = None) -> None:
    """Emit a status event so manager heartbeats stay fresh."""

    from tools.agent import bus_event

    argv = [
        "log",
        "--event",
        "status",
        "--summary",
        summary,
        "--agent",
        manager_id,
    ]
    for item in _parse_meta(extras or []):
        argv.extend(["--extra", item])
    rc = bus_event.main(argv)
    if rc != 0:
        raise RuntimeError(f"heartbeat logging failed with exit code {rc}")


def gather_metrics(metrics_dir: Path) -> dict[str, Any] | None:
    directory = Path(metrics_dir)
    if not directory.exists():
        return None
    metrics_files = sorted(directory.glob("**/metrics.jsonl"))
    entries: list[dict[str, Any]] = []
    for path in metrics_files:
        entries.extend(metrics_summary.load_entries(path))
    if not entries:
        return None
    summary = metrics_summary.summarize(entries)
    summary["files_scanned"] = len(metrics_files)
    return summary


def collect_plan_validation_issues(root: Path | None = None) -> list[dict[str, Any]]:
    base = root or ROOT
    plans_dir = base / "_plans"
    issues: list[dict[str, Any]] = []
    if not plans_dir.exists():
        return issues
    for plan_path in sorted(plans_dir.glob("*.plan.json")):
        try:
            result = validate_plan(plan_path, strict=True)
        except Exception as exc:  # pragma: no cover - defensive
            issues.append(
                {
                    "plan": plan_path.relative_to(base).as_posix(),
                    "errors": [f"validation failed: {exc}"],
                }
            )
            continue
        if result.errors:
            issues.append(
                {
                    "plan": plan_path.relative_to(base).as_posix(),
                    "errors": list(result.errors),
                }
            )
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate manager summary")
    parser.add_argument("--manager", help="Manager agent id")
    parser.add_argument(
        "--log-heartbeat",
        action="store_true",
        help="Emit a status event after generating the report",
    )
    parser.add_argument(
        "--heartbeat-summary",
        default="Manager report generated",
        help="Summary text for the heartbeat event (default: %(default)s)",
    )
    parser.add_argument(
        "--heartbeat-meta",
        action="append",
        default=[],
        help="Additional key=value metadata to attach to the heartbeat event",
    )
    parser.add_argument(
        "--heartbeat-shift",
        help="Shortcut for adding shift=<value> to the heartbeat metadata",
    )
    parser.add_argument(
        "--include-metrics",
        action="store_true",
        help="Append reconciliation metrics summary to the report",
    )
    parser.add_argument(
        "--metrics-dir",
        default=str(ROOT / "_report" / "reconciliation"),
        help="Directory containing reconciliation metrics JSONL files",
    )
    args = parser.parse_args(argv)

    manager_id = args.manager or load_json(MANIFEST := ROOT / "AGENT_MANIFEST.json") or {}
    if isinstance(manager_id, dict):
        manager_id = manager_id.get("agent_id", "manager")
    if not isinstance(manager_id, str):
        manager_id = "manager"

    tasks = load_tasks()
    assignments = collect_assignments()
    claims = collect_claims()
    metrics_data = gather_metrics(Path(args.metrics_dir)) if args.include_metrics else None
    authenticity_data = load_json(AUTH_JSON)
    if not isinstance(authenticity_data, dict):
        authenticity_data = None
    planner_warning_data = planner_queue_warnings.load_queue_warnings(ROOT)
    plan_validation_issues = collect_plan_validation_issues()

    report_path = write_report(
        manager_id,
        tasks,
        assignments,
        claims,
        metrics_data,
        authenticity_data,
        planner_warning_data,
        plan_validation_issues,
    )
    print(f"Manager report written to {report_path.relative_to(ROOT)}")

    if args.log_heartbeat:
        extras = list(args.heartbeat_meta)
        if args.heartbeat_shift:
            extras.append(f"shift={args.heartbeat_shift}")
        try:
            log_heartbeat(manager_id, args.heartbeat_summary, extras=extras)
        except Exception as exc:
            raise SystemExit(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
