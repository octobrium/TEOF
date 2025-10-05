#!/usr/bin/env python3
"""Generate a manager summary of active tasks and receipts."""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from statistics import median

from tools import reconcile_metrics_summary as metrics_summary
from tools.planner import queue_warnings as planner_queue_warnings
from tools.planner.validate import validate_plan

ROOT = Path(__file__).resolve().parents[2]
ASSIGN_DIR = ROOT / "_bus" / "assignments"
CLAIMS_DIR = ROOT / "_bus" / "claims"
MESSAGES_DIR = ROOT / "_bus" / "messages"
REPORT_DIR = ROOT / "_report" / "manager"
TTD_LOG = ROOT / "memory" / "impact" / "ttd.jsonl"
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


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            entries.append(obj)
    return entries


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pct = max(0.0, min(100.0, pct))
    position = (len(ordered) - 1) * (pct / 100.0)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    lower_val = ordered[lower]
    upper_val = ordered[upper]
    return lower_val + (upper_val - lower_val) * (position - lower)


def _format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "n/a"
    sign = "-" if seconds < 0 else ""
    seconds = abs(seconds)
    if seconds < 60:
        return f"{sign}{seconds:.1f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{sign}{minutes:.1f}m"
    hours = minutes / 60
    if hours < 24:
        return f"{sign}{hours:.2f}h"
    days = hours / 24
    return f"{sign}{days:.2f}d"


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


def _load_autonomy_status(base: Path) -> dict[str, Any]:
    data = load_json(base / "_report" / "usage" / "autonomy-status.json")
    return data if isinstance(data, dict) else {}


def _load_anchors(base: Path) -> dict[str, Any]:
    data = load_json(base / "governance" / "anchors.json")
    return data if isinstance(data, dict) else {}


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


def collect_direction_metrics(
    base: Path,
    reconciliation: dict[str, Any] | None,
    authenticity: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    metrics: dict[str, dict[str, Any]] = {}

    latency_entries = load_jsonl(base / "_report" / "usage" / "receipts-latency-latest.jsonl")
    latencies: list[float] = []
    latency_summary: dict[str, Any] | None = None
    for entry in latency_entries:
        if entry.get("kind") == "summary":
            latency_summary = entry
            continue
        if entry.get("kind") != "plan_latency":
            continue
        value = entry.get("latency_seconds", {}).get("plan_to_first_receipt")
        if isinstance(value, (int, float)):
            latencies.append(float(value))
    obs_payload: dict[str, Any] = {
        "plan_to_first_receipt_p95": _percentile(latencies, 95.0),
        "plan_to_first_receipt_median": median(latencies) if latencies else None,
        "sample_size": len(latencies),
    }
    if latency_summary:
        counts = latency_summary.get("counts")
        if isinstance(counts, dict):
            obs_payload["missing_plan_receipts"] = counts.get("plans_with_missing_receipts")
        obs_payload["generated_at"] = latency_summary.get("generated_at")
    metrics["observation.capacity"] = obs_payload

    if reconciliation:
        metrics["coherence.score"] = {
            "match_ratio": reconciliation.get("match_ratio"),
            "difference_total": reconciliation.get("difference_total"),
            "missing_receipt_total": reconciliation.get("missing_receipt_total"),
            "capability_diff_total": reconciliation.get("capability_diff_total"),
            "runs": reconciliation.get("total_runs"),
        }

    plan_entries = load_jsonl(base / "_report" / "usage" / "receipts-index-latest.jsonl")
    total_plans = open_plans = plans_with_missing = 0
    for entry in plan_entries:
        if entry.get("kind") != "plan":
            continue
        total_plans += 1
        status = str(entry.get("status", "")).lower()
        if status not in {"done", "complete", "closed"}:
            open_plans += 1
        missing_list = entry.get("missing_receipts")
        if isinstance(missing_list, list) and missing_list:
            plans_with_missing += 1
    metrics["recursion.depth"] = {
        "open_plans": open_plans,
        "total_plans": total_plans,
        "open_ratio": (open_plans / total_plans) if total_plans else None,
        "plans_with_missing_receipts": plans_with_missing,
    }

    capsule_current = base / "capsule" / "current"
    capsule_target: str | None = None
    capsule_matches = False
    if capsule_current.exists():
        expected = "v1.6"
        if capsule_current.is_symlink():
            try:
                capsule_target = capsule_current.resolve().name
            except Exception:  # pragma: no cover - resolution edge case
                capsule_target = None
        else:
            capsule_target = capsule_current.read_text(encoding="utf-8").strip()
        capsule_matches = capsule_target == expected
    autonomy = _load_autonomy_status(base)
    hygiene = autonomy.get("hygiene") if isinstance(autonomy.get("hygiene"), dict) else {}
    readiness = autonomy.get("readiness") if isinstance(autonomy.get("readiness"), dict) else {}
    metrics["integrity.gap"] = {
        "capsule_target": capsule_target,
        "capsule_matches_expected": capsule_matches,
        "plans_missing_receipts": hygiene.get("plans_with_missing_receipts"),
        "readiness_status": readiness.get("status"),
    }

    quickstart = base / "artifacts" / "ocers_out" / "latest" / "brief.json"
    quickstart_age_hours: float | None = None
    if quickstart.exists():
        mtime = datetime.fromtimestamp(quickstart.stat().st_mtime, timezone.utc)
        quickstart_age_hours = (datetime.now(timezone.utc) - mtime).total_seconds() / 3600.0
    metrics["sustainability.signal"] = {
        "readiness_status": readiness.get("status"),
        "missing_receipts": readiness.get("missing_receipts"),
        "batch_failures": readiness.get("batch_fail_count"),
        "batch_warnings": readiness.get("batch_warn_count"),
        "quickstart_age_hours": quickstart_age_hours,
    }

    anchors = _load_anchors(base)
    events = anchors.get("events") if isinstance(anchors.get("events"), list) else []
    mirror_keys = {
        event.get("key_id")
        for event in events
        if isinstance(event, dict) and event.get("type") == "key" and event.get("key_id")
    }
    optional_payload: dict[str, Any] = {
        "registered_mirrors": len(mirror_keys),
        "overall_trust": None,
    }
    if authenticity and isinstance(authenticity.get("overall_avg_trust"), (int, float)):
        optional_payload["overall_trust"] = authenticity["overall_avg_trust"]
    metrics["optional.safe"] = optional_payload

    return metrics


def append_direction_log(
    metrics: dict[str, dict[str, Any]],
    manager_id: str,
    ts: str,
) -> None:
    if not metrics:
        return
    TTD_LOG.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": ts,
        "manager": manager_id,
        "metrics": metrics,
    }
    with TTD_LOG.open("a", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)
        handle.write("\n")


def write_report(
    ts: str,
    manager_id: str,
    tasks: list[dict[str, Any]],
    assignments: dict[str, Any],
    claims: dict[str, Any],
    metrics: dict[str, Any] | None,
    authenticity: dict[str, Any] | None,
    planner_warnings: list[dict[str, Any]] | None,
    plan_validation_issues: list[dict[str, Any]] | None = None,
    direction_metrics: dict[str, dict[str, Any]] | None = None,
) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
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

    if direction_metrics:
        lines.append("## Direction-of-Travel (TTΔ)")
        label_map = {
            "observation.capacity": "Observation Capacity",
            "coherence.score": "Coherence Score",
            "recursion.depth": "Recursion Depth",
            "integrity.gap": "Integrity Gap",
            "sustainability.signal": "Sustainability",
            "optional.safe": "Safe Optionality",
        }
        order = [
            "observation.capacity",
            "coherence.score",
            "recursion.depth",
            "integrity.gap",
            "sustainability.signal",
            "optional.safe",
        ]
        for key in order:
            payload = direction_metrics.get(key)
            if not payload:
                continue
            label = label_map.get(key, key)
            parts: list[str] = []
            if key == "observation.capacity":
                parts.append(
                    f"plan→first receipt p95={_format_duration(payload.get('plan_to_first_receipt_p95'))}"
                )
                median_val = payload.get("plan_to_first_receipt_median")
                if median_val is not None:
                    parts.append(f"median={_format_duration(median_val)}")
                if payload.get("missing_plan_receipts") is not None:
                    parts.append(f"plans missing receipts={payload['missing_plan_receipts']}")
                if payload.get("sample_size"):
                    parts.append(f"samples={payload['sample_size']}")
            elif key == "coherence.score":
                ratio = payload.get("match_ratio")
                if isinstance(ratio, (int, float)):
                    parts.append(f"match={ratio:.2f}")
                if payload.get("difference_total") is not None:
                    parts.append(f"diffs={payload['difference_total']}")
                if payload.get("missing_receipt_total") is not None:
                    parts.append(f"missing={payload['missing_receipt_total']}")
                if payload.get("capability_diff_total") is not None:
                    parts.append(f"capability={payload['capability_diff_total']}")
                if payload.get("runs") is not None:
                    parts.append(f"runs={payload['runs']}")
            elif key == "recursion.depth":
                total = payload.get("total_plans") or 0
                open_plans = payload.get("open_plans") or 0
                parts.append(f"open={open_plans}/{total}")
                if payload.get("open_ratio") is not None:
                    parts.append(f"open%={payload['open_ratio']:.2f}")
                if payload.get("plans_with_missing_receipts") is not None:
                    parts.append(f"plans missing receipts={payload['plans_with_missing_receipts']}")
            elif key == "integrity.gap":
                target = payload.get("capsule_target") or "n/a"
                parts.append(f"capsule.current→{target}")
                parts.append("match" if payload.get("capsule_matches_expected") else "mismatch")
                if payload.get("plans_missing_receipts") is not None:
                    parts.append(f"hygiene missing plans={payload['plans_missing_receipts']}")
                if payload.get("readiness_status"):
                    parts.append(f"readiness={payload['readiness_status']}")
            elif key == "sustainability.signal":
                if payload.get("readiness_status"):
                    parts.append(f"readiness={payload['readiness_status']}")
                if payload.get("missing_receipts") is not None:
                    parts.append(f"missing_receipts={payload['missing_receipts']}")
                if payload.get("batch_failures") is not None:
                    parts.append(f"batch_failures={payload['batch_failures']}")
                if payload.get("batch_warnings") is not None:
                    parts.append(f"batch_warnings={payload['batch_warnings']}")
                quick_age = payload.get("quickstart_age_hours")
                if isinstance(quick_age, (int, float)):
                    parts.append(f"quickstart_age={quick_age:.2f}h")
                else:
                    parts.append("quickstart_age=n/a")
            elif key == "optional.safe":
                parts.append(f"mirrors={payload.get('registered_mirrors', 0)}")
                trust = payload.get("overall_trust")
                if isinstance(trust, (int, float)):
                    parts.append(f"authenticity={trust:.3f}")
                else:
                    parts.append("authenticity=n/a")
            if not parts:
                parts.append("no data")
            lines.append(f"- **{label}:** {'; '.join(parts)}")
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
    direction_metrics = collect_direction_metrics(ROOT, metrics_data, authenticity_data)

    report_ts = iso_now()
    report_path = write_report(
        report_ts,
        manager_id,
        tasks,
        assignments,
        claims,
        metrics_data,
        authenticity_data,
        planner_warning_data,
        plan_validation_issues,
        direction_metrics,
    )
    print(f"Manager report written to {report_path.relative_to(ROOT)}")

    append_direction_log(direction_metrics, manager_id, report_ts)

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
