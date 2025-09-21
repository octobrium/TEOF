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

from tools.agent import autonomy_latency, autonomy_status, heartbeat, receipts_hygiene, session_brief, task_sync

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"
BATCH_LOG_DIR_NAME = "batch-refinement"


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
    latency_dry_run: bool = False,
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
    log_path.write_text(json.dumps(log_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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

    heartbeat_payload = None
    heartbeat_summary = f"Batch refinement {task.upper()} complete"
    heartbeat_extras = {
        "task": task.upper(),
        "batch_log": str(log_path.relative_to(ROOT)) if log_path.is_relative_to(ROOT) else str(log_path),
        "autonomy_receipt": report["autonomy_status"]["receipt_path"],
        "operator_summary": str(report.get("summary")),
    }
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

    if latency_threshold is not None:
        latency_result = autonomy_latency.check_latency(
            threshold=latency_threshold,
            dry_run=latency_dry_run,
            write=not latency_dry_run,
        )
        report["latency_alerts"] = latency_result["alerts"]
        if latency_result["receipt_path"] is not None:
            receipt_path = latency_result["receipt_path"]
            report["latency_receipt"] = str(receipt_path.relative_to(ROOT)) if receipt_path.is_relative_to(ROOT) else str(receipt_path)
            log_payload["latency_receipt"] = report["latency_receipt"]
        log_payload["latency_alerts"] = latency_result["alerts"]

    log_path.write_text(json.dumps(log_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

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
        help="Emit autonomy latency alerts for plans exceeding this many seconds",
    )
    parser.add_argument(
        "--latency-dry-run",
        action="store_true",
        help="Print latency alerts instead of logging to the bus",
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
            latency_dry_run=args.latency_dry_run,
        )
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise SystemExit(str(exc)) from exc
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
