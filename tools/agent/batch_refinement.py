#!/usr/bin/env python3
"""Run a batch refinement cycle: tests → receipts hygiene → operator preset."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

from tools.agent import receipts_hygiene, session_brief

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
) -> dict:
    resolved_agent = _resolve_agent(agent)
    if not quiet:
        print("Running pytest")
    _run_pytest(pytest_args)

    if not quiet:
        print("Running receipts hygiene bundle")
    summary = receipts_hygiene.run_hygiene(
        root=receipts_hygiene.ROOT,
        output_dir=receipts_hygiene.DEFAULT_USAGE_DIR,
        quiet=True,
        fail_on_missing=fail_on_missing,
        max_plan_latency=max_plan_latency,
    )

    claim = session_brief.load_claim(task.upper())
    report = session_brief._run_operator_preset(  # type: ignore[attr-defined]
        resolved_agent,
        task.upper(),
        claim,
        output=output,
    )

    if not quiet:
        print("Operator preset receipt:")
        print(f"  Summary: {report.get('summary')}")
        print(f"  Receipt: {report.get('receipt_path')}")
    report["receipts_hygiene"] = summary

    log_directory = (log_dir or _default_log_dir()).resolve()
    log_directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = log_directory / f"batch-refinement-{timestamp}.json"

    log_payload = {
        "generated_at": timestamp,
        "task": task.upper(),
        "agent": resolved_agent,
        "pytest_args": pytest_args,
        "operator_preset": {
            "summary": report.get("summary"),
            "receipt_path": report.get("receipt_path"),
        },
        "receipts_hygiene": summary,
    }
    log_path.write_text(json.dumps(log_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["log_path"] = str(log_path.relative_to(ROOT)) if log_path.is_relative_to(ROOT) else str(log_path)

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
        )
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise SystemExit(str(exc)) from exc
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
