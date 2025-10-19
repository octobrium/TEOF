"""Simple background service for coordinator loop.

Watches backlog, runs the loop at intervals, and captures basic
telemetry + error receipts. Intended as the process donors run to lend
their agent seat without manual intervention.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Sequence

from tools.agent import session_guard
from tools.autonomy.shared import write_receipt_payload


ROOT = Path(__file__).resolve().parents[2]
SERVICE_DIR = ROOT / "_report" / "agent"


def _utc_now() -> str:
    return dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _run_loop(args: Sequence[str]) -> int:
    command = ["python3", "-m", "tools.autonomy.coordinator_loop", *args]
    proc = subprocess.run(command, cwd=ROOT, check=False)
    return proc.returncode


def _write_log(agent_id: str, payload: Dict[str, Any]) -> Path:
    directory = SERVICE_DIR / agent_id / "autonomy-coordinator" / "service"
    _ensure_dir(directory)
    timestamp = _utc_now().replace(":", "")
    path = directory / f"run-{timestamp}.json"
    write_receipt_payload(path, payload)
    return path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manager-agent", help="Agent id override")
    parser.add_argument("--worker-agent", help="Worker agent id override")
    parser.add_argument("--interval", type=float, default=60.0, help="Seconds between iterations (default: 60)")
    parser.add_argument("--max-iterations", type=int, default=0, help="Maximum iterations (0 = infinite)")
    parser.add_argument("--no-claim", action="store_true", help="Skip bus_claim step (use when coordinator_loop handles it)")
    parser.add_argument("--once", action="store_true", help="Run a single iteration and exit")
    parser.add_argument("--log", action="store_true", help="Write receipts for each iteration")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    agent_id = session_guard.resolve_agent_id(args.manager_agent)
    iterations = 0
    while True:
        iterations += 1
        session_guard.ensure_recent_session(agent_id, context="coordinator_service")

        loop_args = []
        if args.manager_agent:
            loop_args.extend(["--manager-agent", args.manager_agent])
        if args.worker_agent:
            loop_args.extend(["--worker-agent", args.worker_agent])
        loop_args.extend(["--iterations", "1"])

        exit_code = _run_loop(loop_args)
        payload = {
            "ts": _utc_now(),
            "manager_agent": agent_id,
            "loop_exit_code": exit_code,
            "iterations": iterations,
        }
        if args.log:
            _write_log(agent_id, payload)

        if exit_code != 0:
            print(f"coordinator_service: loop exited with {exit_code}; stopping")
            return exit_code

        if args.once:
            return 0

        if args.max_iterations and iterations >= args.max_iterations:
            return 0

        time.sleep(max(0.0, args.interval))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
