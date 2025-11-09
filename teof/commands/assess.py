from __future__ import annotations

import datetime as dt
import json
from argparse import Namespace
from dataclasses import asdict
from typing import Any, Mapping

from teof import status_report, tasks_report
from teof.commands import scan as scan_cmd
from tools.autonomy import critic as critic_mod
from tools.autonomy import ethics_gate as ethics_mod
from tools.autonomy import frontier as frontier_mod
from tools.autonomy import tms as tms_mod


def _utc_now() -> str:
    return dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _collect_status_payload() -> Mapping[str, Any]:
    root = status_report.ROOT
    log_flag = root.resolve() == status_report.ROOT.resolve()
    return status_report.build_status_payload(root, log=log_flag)


def _collect_scan_summary(limit: int) -> dict[str, Any]:
    limit = max(1, limit)
    frontier_entries = frontier_mod.compute_frontier(limit=limit)
    critic_anomalies = critic_mod.detect_anomalies()
    tms_conflicts = tms_mod.detect_conflicts()
    ethics_violations = ethics_mod.detect_violations()

    counts = {
        "frontier": len(frontier_entries),
        "critic": len(critic_anomalies),
        "tms": len(tms_conflicts),
        "ethics": len(ethics_violations),
    }
    payload = {
        "generated_at": _utc_now(),
        "base_root": str(scan_cmd._scan_root()),
        "components": scan_cmd.SCAN_COMPONENTS,
        "counts": counts,
        "frontier": [entry.as_dict() for entry in frontier_entries[:limit]],
        "critic": critic_anomalies[:limit],
        "tms": tms_conflicts[:limit],
        "ethics": ethics_violations[:limit],
    }
    return payload


def _collect_task_summary(limit: int) -> dict[str, Any]:
    limit = max(1, limit)
    records = tasks_report.collect_tasks()
    open_tasks = tasks_report.filter_open_tasks(records)
    ordered = tasks_report.sort_tasks(open_tasks)
    summary = tasks_report.summarize_tasks(ordered)
    warnings = tasks_report.compute_warnings(ordered)
    top_records = [asdict(record) for record in ordered[:limit]]
    payload = {
        "generated_at": _utc_now(),
        "summary": summary,
        "warnings": warnings,
        "top_tasks": top_records,
    }
    return payload


def _render_status_lines(payload: Mapping[str, Any]) -> list[str]:
    lines: list[str] = []
    lines.append("## Status Snapshot")
    for entry in payload.get("snapshot", []) or []:
        lines.append(f"- {entry}")
    lines.append("")
    lines.append("## Autonomy Footprint")
    autonomy = payload.get("autonomy_footprint") or {}
    metrics = autonomy.get("metrics") if isinstance(autonomy, Mapping) else {}
    baseline = autonomy.get("baseline") if isinstance(autonomy, Mapping) else {}
    module_files = metrics.get("module_files", 0)
    loc = metrics.get("loc", 0)
    helper_defs = metrics.get("helper_defs", 0)
    receipts = metrics.get("receipt_count", 0)
    baseline_modules = baseline.get("module_files", "–") if isinstance(baseline, Mapping) else "–"
    baseline_loc = baseline.get("loc", "–") if isinstance(baseline, Mapping) else "–"
    baseline_helpers = baseline.get("helper_defs", "–") if isinstance(baseline, Mapping) else "–"
    lines.append(
        f"- Modules: {module_files} (baseline {baseline_modules}) · "
        f"LOC: {loc} (baseline {baseline_loc}) · "
        f"Helpers: {helper_defs} (baseline {baseline_helpers}) · "
        f"Autonomy receipts: {receipts}"
    )
    cli = payload.get("cli_capability") or {}
    automation = payload.get("automation_health") or {}
    if isinstance(cli, Mapping):
        lines.append(
            "- CLI health: "
            + ", ".join(
                [
                    f"commands={cli.get('commands', '?')}",
                    f"missing_tests={cli.get('missing_tests', '?')}",
                    f"stale>{cli.get('stale_over_threshold', 0)}d",
                ]
            )
        )
    else:
        lines.append("- CLI health:")
        for entry in cli if isinstance(cli, list) else []:
            lines.append(f"  {entry}")

    if isinstance(automation, Mapping):
        lines.append(
            "- Automation: "
            + ", ".join(
                [
                    f"modules={automation.get('modules', '?')}",
                    f"missing_receipts={automation.get('missing_receipts', '?')}",
                    f"stale={automation.get('stale_over_threshold', '?')}",
                ]
            )
        )
    else:
        lines.append("- Automation:")
        for entry in automation if isinstance(automation, list) else []:
            lines.append(f"  {entry}")
    return lines


def _render_frontier_lines(scan_payload: Mapping[str, Any]) -> list[str]:
    lines = ["", "## Frontier / Guards"]
    counts = scan_payload.get("counts", {})
    lines.append(
        "- Counts: "
        + ", ".join(
            f"{name}={counts.get(name, 0)}" for name in ("frontier", "critic", "tms", "ethics")
        )
    )
    frontier = scan_payload.get("frontier") or []
    if frontier:
        lines.append("- Top frontier items:")
        for entry in frontier:
            ident = entry.get("id", "?")
            title = entry.get("title", "?")
            score = entry.get("score")
            plan_id = entry.get("plan_id") or "-"
            if isinstance(score, (int, float)):
                score_display = f"{score:.2f}"
            else:
                score_display = "n/a"
            lines.append(f"  - {ident} ({plan_id}): {title} — score {score_display}")
    else:
        lines.append("- No frontier entries")
    return lines


def _render_task_lines(task_payload: Mapping[str, Any]) -> list[str]:
    lines = ["", "## Open Tasks"]
    summary = task_payload.get("summary", {})
    lines.append(
        "- Totals: "
        + ", ".join(
            [
                f"total={summary.get('total', 0)}",
                f"open={summary.get('status', {}).get('open', 0)}",
                f"untracked={summary.get('status', {}).get('untracked', 0)}",
            ]
        )
    )
    top_tasks = task_payload.get("top_tasks") or []
    if top_tasks:
        lines.append("- Top items:")
        for task in top_tasks:
            lines.append(
                f"  - {task['task_id']}: {task['title']} "
                f"(status={task['status']}, plan={task.get('plan_id') or '-'})"
            )
    warnings = task_payload.get("warnings") or []
    lines.append("")
    lines.append("## Task Warnings")
    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- none")
    return lines


def _render_text(
    status_payload: Mapping[str, Any],
    scan_payload: Mapping[str, Any],
    task_payload: Mapping[str, Any],
) -> str:
    timestamp = status_payload.get("generated_at", _utc_now())
    lines = [f"# TEOF Assess ({timestamp})", ""]
    lines.extend(_render_status_lines(status_payload))
    lines.extend(_render_frontier_lines(scan_payload))
    lines.extend(_render_task_lines(task_payload))
    return "\n".join(lines)


def run(args: Namespace) -> int:
    fmt = getattr(args, "format", "text").lower()
    frontier_limit = max(1, getattr(args, "frontier_limit", 5))
    task_limit = max(1, getattr(args, "task_limit", 5))

    status_payload = _collect_status_payload()
    scan_payload = _collect_scan_summary(frontier_limit)
    task_payload = _collect_task_summary(task_limit)

    if fmt == "json":
        payload = {
            "generated_at": _utc_now(),
            "status": status_payload,
            "scan": scan_payload,
            "tasks": task_payload,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(_render_text(status_payload, scan_payload, task_payload))
    return 0


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    import argparse

    parser = subparsers.add_parser(
        "assess",
        help="Synthesize status, scan, and task telemetry for a quick health check",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--frontier-limit",
        type=int,
        default=5,
        help="How many frontier entries to include (default: 5)",
    )
    parser.add_argument(
        "--task-limit",
        type=int,
        default=5,
        help="How many open tasks to include (default: 5)",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
