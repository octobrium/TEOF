#!/usr/bin/env python3
"""Run a batch refinement cycle: tests → receipts hygiene → operator preset."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from tools.agent import (
    autonomy_latency,
    autonomy_status,
    backlog_health,
    confidence_watch,
    heartbeat,
    receipts_hygiene,
    session_brief,
    task_sync,
)

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"
BATCH_LOG_DIR_NAME = "batch-refinement"
CONFIDENCE_REPORT_DIR = ROOT / "_report" / "usage" / "confidence-watch"


def _run_pytest(pytest_args: List[str]) -> None:
    cmd = [sys.executable, "-m", "pytest"] + pytest_args
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"pytest failed with exit code {result.returncode}")


def _load_manifest_agent() -> Optional[str]:
    if not MANIFEST_PATH.exists():
        return None
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    agent = data.get("agent_id")
    if isinstance(agent, str) and agent.strip():
        return agent.strip()
    return None


def _resolve_agent(agent: Optional[str]) -> str:
    if agent and agent.strip():
        return agent.strip()
    manifest_agent = _load_manifest_agent()
    if manifest_agent:
        return manifest_agent
    raise SystemExit("agent id required; provide --agent or populate AGENT_MANIFEST.json")


def _default_log_dir() -> Path:
    usage_dir = receipts_hygiene.DEFAULT_USAGE_DIR
    return usage_dir / BATCH_LOG_DIR_NAME


def _load_batch_logs(log_dir: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not log_dir.exists():
        return entries
    for path in sorted(log_dir.glob("batch-refinement-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        payload["_path"] = path
        entries.append(payload)
    return entries


def _write_batch_summary(log_dir: Path) -> tuple[dict[str, Any], Path] | tuple[None, None]:
    logs = _load_batch_logs(log_dir)
    if not logs:
        return None, None

    total_runs = len(logs)
    pytest_total = 0.0
    hygiene_total = 0.0
    duration_count = 0
    missing_receipt_runs = 0
    latency_alert_runs = 0
    last_failure = None

    for entry in logs:
        metrics = entry.get("metrics") or {}
        pytest_seconds = metrics.get("pytest_seconds")
        hygiene_seconds = metrics.get("hygiene_seconds")
        if isinstance(pytest_seconds, (int, float)) and isinstance(hygiene_seconds, (int, float)):
            duration_count += 1
            pytest_total += pytest_seconds
            hygiene_total += hygiene_seconds
        missing = metrics.get("missing_receipts")
        if isinstance(missing, int) and missing > 0:
            missing_receipt_runs += 1
        if entry.get("latency_alerts"):
            latency_alert_runs += 1
        summary_field = entry.get("operator_preset", {}).get("summary")
        if summary_field in {"fail", "error"}:
            last_failure = entry.get("generated_at")

    avg_pytest = pytest_total / duration_count if duration_count else None
    avg_hygiene = hygiene_total / duration_count if duration_count else None

    last_path = logs[-1]["_path"]
    try:
        last_rel = str(last_path.relative_to(ROOT))
    except (ValueError, AttributeError):
        last_rel = str(last_path)

    summary_payload = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_runs": total_runs,
        "average": {
            "pytest_seconds": avg_pytest,
            "hygiene_seconds": avg_hygiene,
        },
        "missing_receipt_runs": missing_receipt_runs,
        "latency_alert_runs": latency_alert_runs,
        "last_failure_at": last_failure,
        "latest_log": {
            "generated_at": logs[-1].get("generated_at"),
            "agent": logs[-1].get("agent"),
            "summary": logs[-1].get("operator_preset", {}).get("summary"),
            "log_path": last_rel,
        },
    }

    summary_path = log_dir / "summary.json"
    summary_path.write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary_payload, summary_path


def _relative_to_root(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _run_backlog_health_guard(threshold: int, candidate_limit: int) -> tuple[dict[str, Any], bool]:
    if threshold < 0:
        raise SystemExit("backlog threshold must be zero or positive")
    if candidate_limit < 0:
        raise SystemExit("backlog candidate limit must be zero or positive")
    data = backlog_health.load_next_development(backlog_health.NEXT_DEV_PATH)
    metrics = backlog_health.compute_metrics(
        data,
        threshold=threshold,
        queue_dir=backlog_health.QUEUE_DIR,
        candidate_limit=candidate_limit,
    )
    receipt_path = backlog_health.write_receipt(metrics, threshold, None)
    payload = {
        "metrics": metrics,
        "receipt_path": _relative_to_root(receipt_path),
    }
    breached = bool(metrics.get("pending_threshold_breached"))
    return payload, breached


def _run_confidence_watch_guard(
    warn_threshold: float,
    window: int,
    min_count: int,
    alert_ratio: float,
    report_dir: Path,
) -> tuple[dict[str, Any], bool]:
    if not 0.0 <= warn_threshold <= 1.0:
        raise SystemExit("confidence warn threshold must be between 0.0 and 1.0")
    if not 0.0 <= alert_ratio <= 1.0:
        raise SystemExit("confidence alert ratio must be between 0.0 and 1.0")
    if window < 0:
        raise SystemExit("confidence window must be zero or positive")
    if min_count < 1:
        raise SystemExit("confidence min-count must be at least 1")

    _, report, written = confidence_watch.run_watch(
        warn_threshold=warn_threshold,
        window=window,
        min_count=min_count,
        alert_ratio=alert_ratio,
        report_dir=report_dir,
    )
    payload: dict[str, Any] = {
        "report": report,
        "report_path": _relative_to_root(written) if written is not None else None,
    }
    alerts = bool(report.get("alerts"))
    return payload, alerts


def _refresh_autonomy_status(logs: List[Dict[str, Any]]) -> tuple[Dict[str, Any], Path]:
    """Write the autonomy status summary and return payload/path."""

    hygiene = autonomy_status.load_hygiene()
    summary = autonomy_status.summarise(hygiene, logs)
    payload: Dict[str, Any] = dict(summary)
    if logs:
        entries_detail: List[Dict[str, Any]] = []
        for entry in logs:
            detail = {
                "generated_at": entry.get("generated_at"),
                "summary": entry.get("operator_preset", {}).get("summary"),
                "agent": entry.get("agent"),
            }
            path = entry.get("_path")
            if isinstance(path, Path):
                try:
                    detail["log_path"] = str(path.relative_to(ROOT))
                except ValueError:
                    detail["log_path"] = str(path)
            entries_detail.append(detail)
        payload.setdefault("batch_logs", {})["entries_detail"] = entries_detail

    target = autonomy_status.ROOT / "_report" / "usage" / "autonomy-status.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload, target


def run_batch(
    *,
    task: str,
    agent: Optional[str],
    pytest_args: List[str],
    quiet: bool,
    output: Optional[str],
    log_dir: Optional[Path] = None,
    fail_on_missing: bool = False,
    max_plan_latency: Optional[float] = None,
    latency_threshold: Optional[float] = None,
    latency_warn_threshold: Optional[float] = None,
    latency_fail_threshold: Optional[float] = None,
    latency_dry_run: bool = False,
    backlog_threshold: int = backlog_health.DEFAULT_THRESHOLD,
    backlog_candidate_limit: int = backlog_health.DEFAULT_CANDIDATE_LIMIT,
    allow_backlog_breach: bool = False,
    skip_backlog_guard: bool = False,
    confidence_warn_threshold: float = 0.9,
    confidence_window: int = 10,
    confidence_min_count: int = 5,
    confidence_alert_ratio: float = 0.6,
    allow_confidence_alerts: bool = False,
    skip_confidence_watch: bool = False,
) -> dict:
    resolved_agent = _resolve_agent(agent)
    if not quiet:
        print("Running pytest")
    import time

    start_ts = time.perf_counter()
    _run_pytest(pytest_args)
    pytest_duration = time.perf_counter() - start_ts

    if not quiet:
        print("Running receipts hygiene bundle")
    summary = receipts_hygiene.run_hygiene(
        root=receipts_hygiene.ROOT,
        output_dir=receipts_hygiene.DEFAULT_USAGE_DIR,
        quiet=True,
        fail_on_missing=fail_on_missing,
        max_plan_latency=max_plan_latency,
        warn_plan_latency=receipts_hygiene.DEFAULT_WARN_THRESHOLD,
        fail_plan_latency=receipts_hygiene.DEFAULT_FAIL_THRESHOLD,
    )
    hygiene_duration = time.perf_counter() - (start_ts + pytest_duration)

    claim = session_brief.load_claim(task.upper())
    report = session_brief._run_operator_preset(  # type: ignore[attr-defined]
        resolved_agent,
        task.upper(),
        claim,
        output=output,
    )

    if not quiet:
        print("Running task_sync")
    try:
        task_sync_changes = task_sync.sync_tasks()
    except Exception as exc:  # pragma: no cover - defensive
        raise SystemExit(f"task_sync failed: {exc}") from exc

    if not quiet:
        print("Operator preset receipt:")
        print(f"  Summary: {report.get('summary')}")
        print(f"  Receipt: {report.get('receipt_path')}")
    report["receipts_hygiene"] = summary
    report["task_sync"] = {"changes": task_sync_changes}

    log_directory = (log_dir or _default_log_dir()).resolve()
    log_directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = log_directory / f"batch-refinement-{timestamp}.json"

    metrics_summary = {}
    if isinstance(summary, dict):
        metrics_value = summary.get("metrics")
        if isinstance(metrics_value, dict):
            metrics_summary = metrics_value

    log_payload = {
        "generated_at": timestamp,
        "task": task.upper(),
        "agent": resolved_agent,
        "pytest_args": pytest_args,
        "metrics": {
            "pytest_seconds": pytest_duration,
            "hygiene_seconds": hygiene_duration,
            "missing_receipts": metrics_summary.get("plans_missing_receipts"),
            "slow_plan_count": len(metrics_summary.get("slow_plans") or []),
        },
        "operator_preset": {
            "summary": report.get("summary"),
            "receipt_path": report.get("receipt_path"),
        },
        "receipts_hygiene": summary,
        "task_sync_changes": task_sync_changes,
    }
    report["log_path"] = str(log_path.relative_to(ROOT)) if log_path.is_relative_to(ROOT) else str(log_path)

    logs_for_summary = autonomy_status.load_batch_logs()
    default_log_dir = _default_log_dir().resolve()
    if log_directory != default_log_dir:
        log_payload_for_summary = dict(log_payload)
        log_payload_for_summary["_path"] = log_path
        logs_for_summary.append(log_payload_for_summary)

    auto_summary, auto_path = _refresh_autonomy_status(logs_for_summary)
    report["autonomy_status"] = {
        "summary": auto_summary,
        "receipt_path": str(auto_path.relative_to(ROOT))
        if auto_path.is_relative_to(ROOT)
        else str(auto_path),
    }
    log_payload["autonomy_status_receipt"] = report["autonomy_status"]["receipt_path"]
    log_payload["autonomy_status_summary"] = auto_summary

    guard_failures: list[str] = []

    if not skip_backlog_guard:
        backlog_payload, backlog_breached = _run_backlog_health_guard(
            backlog_threshold,
            backlog_candidate_limit,
        )
        report["backlog_health"] = backlog_payload
        log_payload["backlog_health"] = backlog_payload
        if backlog_breached:
            report.setdefault("alerts", []).append("backlog_depleted")
            if not allow_backlog_breach:
                guard_failures.append(
                    "backlog health guard breached: pending items below threshold (Observation→Self-repair)"
                )

    if not skip_confidence_watch:
        confidence_payload, alerts_flag = _run_confidence_watch_guard(
            confidence_warn_threshold,
            confidence_window,
            confidence_min_count,
            confidence_alert_ratio,
            CONFIDENCE_REPORT_DIR,
        )
        report["confidence_watch"] = confidence_payload
        log_payload["confidence_watch"] = confidence_payload
        if alerts_flag:
            report.setdefault("alerts", []).append("confidence_alert")
            if not allow_confidence_alerts:
                guard_failures.append(
                    "confidence watch raised alerts: overconfidence ratio above threshold (Truth→Ethics)"
                )

    log_path.write_text(json.dumps(log_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    heartbeat_payload = None
    heartbeat_summary = f"Batch refinement {task.upper()} complete"
    heartbeat_extras = {
        "task": task.upper(),
        "batch_log": str(log_path.relative_to(ROOT)) if log_path.is_relative_to(ROOT) else str(log_path),
        "autonomy_receipt": report["autonomy_status"]["receipt_path"],
        "operator_summary": str(report.get("summary")),
    }
    if not guard_failures:
        try:
            heartbeat_payload = heartbeat.emit_status(
                resolved_agent,
                heartbeat_summary,
                extras=heartbeat_extras,
            )
        except Exception as exc:  # pragma: no cover - defensive
            if not quiet:
                print(f"Heartbeat emission failed: {exc}")

        if heartbeat_payload:
            report["heartbeat"] = heartbeat_payload
            log_payload["heartbeat"] = heartbeat_payload

    if latency_threshold is not None or latency_warn_threshold is not None or latency_fail_threshold is not None:
        latency_result = autonomy_latency.check_latency(
            threshold=latency_threshold,
            warn_threshold=latency_warn_threshold,
            fail_threshold=latency_fail_threshold,
            dry_run=latency_dry_run,
            write=not latency_dry_run,
        )
        report["latency_alerts"] = latency_result["alerts"]
        receipt_path = latency_result.get("receipt_path")
        if receipt_path is not None:
            report["latency_receipt"] = (
                str(receipt_path.relative_to(ROOT))
                if receipt_path.is_relative_to(ROOT)
                else str(receipt_path)
            )
            log_payload["latency_receipt"] = report["latency_receipt"]
        log_payload["latency_alerts"] = latency_result["alerts"]

    log_path.write_text(json.dumps(log_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary_payload, summary_path = _write_batch_summary(log_directory)
    if summary_payload is not None and summary_path is not None:
        report["batch_summary"] = {
            "path": str(summary_path.relative_to(ROOT)) if summary_path.is_relative_to(ROOT) else str(summary_path),
            "metrics": summary_payload,
        }
        log_payload["batch_summary"] = report["batch_summary"]
        log_path.write_text(json.dumps(log_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if guard_failures:
        raise SystemExit("; ".join(guard_failures))
    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, help="Task identifier (e.g., QUEUE-123)")
    parser.add_argument("--agent", help="Agent id (defaults to AGENT_MANIFEST.json)")
    parser.add_argument(
        "--pytest-args",
        nargs=argparse.REMAINDER,
        default=["-q"],
        help="Arguments passed to pytest (default: -q)",
    )
    parser.add_argument("--output", help="Custom path for operator preset receipt")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")
    parser.add_argument("--log-dir", help="Override log directory for batch receipts")
    parser.add_argument("--fail-on-missing", action="store_true", help="Fail batch when receipts hygiene reports missing evidence")
    parser.add_argument(
        "--max-plan-latency",
        type=float,
        help="Fail batch when plan latency exceeds this many seconds",
    )
    parser.add_argument(
        "--latency-threshold",
        type=float,
        help="Legacy single threshold forwarded to autonomy_latency",
    )
    parser.add_argument(
        "--latency-warn-threshold",
        type=float,
        help="Warn threshold forwarded to autonomy_latency (seconds)",
    )
    parser.add_argument(
        "--latency-fail-threshold",
        type=float,
        help="Fail threshold forwarded to autonomy_latency (seconds)",
    )
    parser.add_argument(
        "--latency-dry-run",
        action="store_true",
        help="Print latency alerts instead of logging to the bus",
    )
    parser.add_argument(
        "--skip-backlog-guard",
        action="store_true",
        help="Skip backlog health guard (not recommended)",
    )
    parser.add_argument(
        "--allow-backlog-breach",
        action="store_true",
        help="Do not fail the batch when backlog health breaches the threshold",
    )
    parser.add_argument(
        "--backlog-threshold",
        type=int,
        default=backlog_health.DEFAULT_THRESHOLD,
        help="Pending item threshold before backlog guard fails (default matches backlog_health CLI)",
    )
    parser.add_argument(
        "--backlog-candidate-limit",
        type=int,
        default=backlog_health.DEFAULT_CANDIDATE_LIMIT,
        help="Number of queue candidates to surface when backlog is low (default matches backlog_health CLI)",
    )
    parser.add_argument(
        "--skip-confidence-watch",
        action="store_true",
        help="Skip confidence watch guard (not recommended)",
    )
    parser.add_argument(
        "--allow-confidence-alerts",
        action="store_true",
        help="Do not fail the batch when confidence watch raises alerts",
    )
    parser.add_argument(
        "--confidence-warn-threshold",
        type=float,
        default=0.9,
        help="Confidence value treated as high (default: 0.9)",
    )
    parser.add_argument(
        "--confidence-window",
        type=int,
        default=10,
        help="Recent entry window for confidence watch (default: 10; 0 = entire log)",
    )
    parser.add_argument(
        "--confidence-min-count",
        type=int,
        default=5,
        help="Minimum entries required before alerts can trigger (default: 5)",
    )
    parser.add_argument(
        "--confidence-alert-ratio",
        type=float,
        default=0.6,
        help="Fraction of high-confidence entries required for alert (default: 0.6)",
    )
    args = parser.parse_args(argv)

    try:
        run_batch(
            task=args.task,
            agent=args.agent,
            pytest_args=args.pytest_args,
            quiet=args.quiet,
            output=args.output,
            log_dir=Path(args.log_dir).resolve() if args.log_dir else None,
            fail_on_missing=args.fail_on_missing,
            max_plan_latency=args.max_plan_latency,
            latency_threshold=args.latency_threshold,
            latency_warn_threshold=args.latency_warn_threshold,
            latency_fail_threshold=args.latency_fail_threshold,
            latency_dry_run=args.latency_dry_run,
            backlog_threshold=args.backlog_threshold,
            backlog_candidate_limit=args.backlog_candidate_limit,
            allow_backlog_breach=args.allow_backlog_breach,
            skip_backlog_guard=args.skip_backlog_guard,
            confidence_warn_threshold=args.confidence_warn_threshold,
            confidence_window=args.confidence_window,
            confidence_min_count=args.confidence_min_count,
            confidence_alert_ratio=args.confidence_alert_ratio,
            allow_confidence_alerts=args.allow_confidence_alerts,
            skip_confidence_watch=args.skip_confidence_watch,
        )
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise SystemExit(str(exc)) from exc
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
