"""Autonomy stress-test harness that uses TEOF CLIs to advance a plan step.

This lives in the exploratory lane and intentionally leans on existing guardrails
(`teof frontier|critic|tms|scan`, `plan_scope`, planner validator, policy checks)
so automation is literally using TEOF to improve TEOF.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLAN = "exploratory/2025-11-09-autonomy-stress-test"
DEFAULT_RECEIPT_DIR = Path("_report/exploratory/autonomy-stress-test")
SYSTEMIC_SCAN_POINTER = Path("_report/usage/systemic-scan/ratchet-history.jsonl")
MEMORY_LOG = Path("memory/log.jsonl")


@dataclass
class CommandSpec:
    name: str
    argv: list[str]
    critical: bool = False


def _sha256(path: Path) -> str | None:
    if not (REPO_ROOT / path).exists():
        return None
    digest = hashlib.sha256()
    with (REPO_ROOT / path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tail_matches(path: Path, needle: str, limit: int = 5) -> list[str]:
    target = REPO_ROOT / path
    if not target.exists():
        return []
    matches: list[str] = []
    with target.open("r", encoding="utf-8") as handle:
        for line in handle:
            if needle in line:
                matches.append(line.strip())
    return matches[-limit:]


def _truncate(text: str, limit: int = 4000) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _resolve_plan_path(plan_arg: str) -> Path:
    if plan_arg.endswith(".json"):
        return REPO_ROOT / plan_arg
    return REPO_ROOT / "_plans" / f"{plan_arg}.plan.json"


def _load_baseline(path: Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    absolute = REPO_ROOT / path
    if not absolute.exists():
        return None
    with absolute.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _run_command(spec: CommandSpec) -> dict[str, Any]:
    start = time.monotonic()
    proc = subprocess.run(
        spec.argv,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    duration = time.monotonic() - start
    return {
        "name": spec.name,
        "argv": spec.argv,
        "exit_code": proc.returncode,
        "duration_sec": round(duration, 3),
        "stdout": _truncate(proc.stdout),
        "stderr": _truncate(proc.stderr),
        "critical": spec.critical,
    }


def _emit_bus_dissent(agent: str, plan_ref: str, summary: str) -> dict[str, Any]:
    argv = [
        sys.executable,
        "-m",
        "teof",
        "bus_event",
        "log",
        "--event",
        "dissent",
        "--summary",
        summary,
        "--plan",
        plan_ref,
        "--agent",
        agent,
    ]
    result = _run_command(CommandSpec("bus_event", argv))
    return result


def run(plan: str, step: str, receipt_dir: Path, baseline: Path | None, agent: str | None) -> Path:
    plan_path = _resolve_plan_path(plan)
    if not plan_path.exists():
        raise SystemExit(f"plan file not found: {plan_path}")
    timestamp = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    baseline_data = _load_baseline(baseline)

    memory_hash = _sha256(MEMORY_LOG)
    systemic_hash = _sha256(SYSTEMIC_SCAN_POINTER)
    observation_drift = False
    if baseline_data:
        obs = baseline_data.get("observation", {})
        if obs.get("memory_hash") and obs["memory_hash"] != memory_hash:
            observation_drift = True
        if obs.get("systemic_scan_hash") and obs["systemic_scan_hash"] != systemic_hash:
            observation_drift = True

    commands: list[dict[str, Any]] = []
    break_reasons: list[str] = []

    python = sys.executable
    specs = [
        CommandSpec(
            "plan_scope",
            [python, "-m", "teof", "plan_scope", "--plan", plan, "--format", "json", "--no-receipt"],
        ),
        CommandSpec("frontier", [python, "-m", "teof", "frontier", "--format", "json"]),
        CommandSpec("critic", [python, "-m", "teof", "critic", "--format", "json"]),
        CommandSpec("tms", [python, "-m", "teof", "tms", "--format", "json"]),
        CommandSpec(
            "scan_summary",
            [python, "-m", "teof", "scan", "--summary", "--no-history"],
            critical=True,
        ),
        CommandSpec(
            "planner_validate",
            [python, "tools/planner/validate.py", "--strict"],
            critical=True,
        ),
        CommandSpec(
            "policy_checks",
            ["bash", "scripts/policy_checks.sh"],
            critical=True,
        ),
    ]

    for spec in specs:
        result = _run_command(spec)
        commands.append(result)
        if result["exit_code"] != 0 and spec.critical:
            break_reasons.append(f"{spec.name} failed ({result['exit_code']})")

    if observation_drift:
        break_reasons.append("observation_drift_detected")

    receipt_dir = (REPO_ROOT / receipt_dir).resolve()
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = receipt_dir / f"harness-{timestamp.replace(':', '').replace('-', '')}.json"

    git_status = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    receipt = {
        "plan": plan,
        "plan_path": str(plan_path.relative_to(REPO_ROOT)),
        "step": step,
        "timestamp": timestamp,
        "observation": {
            "memory_hash": memory_hash,
            "systemic_scan_hash": systemic_hash,
            "memory_matches": _tail_matches(MEMORY_LOG, plan.split("/")[-1]),
            "observation_drift": observation_drift,
            "baseline": str(baseline) if baseline else None,
        },
        "commands": commands,
        "break_detected": bool(break_reasons),
        "break_reasons": break_reasons,
        "git_status": git_status.stdout.strip(),
    }

    if observation_drift and agent:
        commands.append(_emit_bus_dissent(agent, plan, "Observation drift detected during autonomy stress run"))

    with receipt_path.open("w", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2)
        handle.write("\n")

    if receipt["break_detected"]:
        print(f"[break] {receipt_path}")
    else:
        print(f"[ok] {receipt_path}")
    return receipt_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Autonomy stress harness (exploratory lane).")
    parser.add_argument("--plan", default=DEFAULT_PLAN, help="Plan identifier or explicit path.")
    parser.add_argument("--step", default="S2", help="Plan step identifier to annotate.")
    parser.add_argument(
        "--receipt-dir",
        default=str(DEFAULT_RECEIPT_DIR),
        help="Directory for harness receipts (relative to repo root).",
    )
    parser.add_argument(
        "--baseline",
        help="Optional prior receipt path for observation drift comparison (relative to repo root).",
    )
    parser.add_argument(
        "--agent",
        help="Agent id to use when emitting bus dissent events on drift (optional).",
    )
    args = parser.parse_args()
    receipt_dir = Path(args.receipt_dir)
    baseline = Path(args.baseline) if args.baseline else None
    run(plan=args.plan, step=args.step, receipt_dir=receipt_dir, baseline=baseline, agent=args.agent)


if __name__ == "__main__":
    main()
