"""Coordinator manager service.

Supervises one or more worker agents by invoking the coordinator loop for
each in turn, recording receipts, and stopping when guardrails fail. This
allows a single manager seat to keep multiple donated workers productive
without manual orchestration.
"""
from __future__ import annotations

import argparse
import datetime as dt
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Sequence

from tools.agent import session_guard
from tools.autonomy import coordinator_loop
from tools.autonomy.shared import write_receipt_payload


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RECEIPT_DIR = ROOT / "_report" / "agent"


def _utc_now() -> str:
    return dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workers",
        nargs="+",
        required=True,
        help="Worker agent ids to supervise (space-separated)",
    )
    parser.add_argument("--manager-agent", help="Manager agent id override (defaults to manifest)")
    parser.add_argument("--interval", type=float, default=60.0, help="Seconds to sleep between rounds (default: 60)")
    parser.add_argument("--max-rounds", type=int, default=0, help="Maximum rounds to execute (0 = infinite)")
    parser.add_argument("--dry-run", action="store_true", help="Print planned actions without executing")
    parser.add_argument("--log", action="store_true", help="Write receipts for each round")
    parser.add_argument(
        "--allow-worker-stale",
        action="store_true",
        help="Allow worker session overrides (passes through to coordinator loop)",
    )
    return parser.parse_args(argv)


def _run_worker(manager_agent: str, worker_agent: str, *, allow_worker_stale: bool, dry_run: bool) -> Dict[str, Any]:
    loop_args = [
        "--manager-agent",
        manager_agent,
        "--worker-agent",
        worker_agent,
        "--iterations",
        "1",
    ]
    if allow_worker_stale:
        loop_args.append("--allow-worker-stale")
    if dry_run:
        loop_args.append("--dry-run")

    exit_code = coordinator_loop.main(loop_args)
    return {
        "worker": worker_agent,
        "exit_code": exit_code,
    }


def _write_receipt(manager_agent: str, payload: Dict[str, Any]) -> Path:
    base = DEFAULT_RECEIPT_DIR / manager_agent / "autonomy-coordinator" / "manager"
    _ensure_dir(base)
    timestamp = _utc_now().replace(":", "")
    path = base / f"manager-round-{timestamp}.json"
    write_receipt_payload(path, payload)
    return path


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    manager_agent = session_guard.resolve_agent_id(args.manager_agent)
    rounds = 0

    while True:
        rounds += 1
        session_guard.ensure_recent_session(manager_agent, context="manager_service")

        round_payload: Dict[str, Any] = {
            "generated_at": _utc_now(),
            "manager_agent": manager_agent,
            "round": rounds,
            "results": [],
            "dry_run": bool(args.dry_run),
        }

        for worker in args.workers:
            result = _run_worker(
                manager_agent,
                worker,
                allow_worker_stale=args.allow_worker_stale,
                dry_run=args.dry_run,
            )
            round_payload["results"].append(result)
            if not args.dry_run and result["exit_code"] != 0:
                round_payload["circuit_breaker"] = {
                    "active": True,
                    "reason": "worker_exit",
                    "worker": worker,
                    "exit_code": result["exit_code"],
                }
                if args.log:
                    _write_receipt(manager_agent, round_payload)
                print(f"manager_service: worker {worker} exited with {result['exit_code']}; stopping")
                return result["exit_code"]

        if args.log:
            _write_receipt(manager_agent, round_payload)

        if args.dry_run or (args.max_rounds and rounds >= args.max_rounds):
            return 0

        time.sleep(max(0.0, args.interval))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
