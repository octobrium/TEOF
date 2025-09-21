#!/usr/bin/env python3
"""Run a batch refinement cycle: tests → receipts hygiene → operator preset."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from tools.agent import receipts_hygiene, session_brief

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"


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


def run_batch(*, task: str, agent: Optional[str], pytest_args: List[str], quiet: bool, output: Optional[str]) -> dict:
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
    args = parser.parse_args(argv)

    try:
        run_batch(
            task=args.task,
            agent=args.agent,
            pytest_args=args.pytest_args,
            quiet=args.quiet,
            output=args.output,
        )
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise SystemExit(str(exc)) from exc
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
