"""Coordinator loop that picks backlog items and runs orchestrator."""
from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any, Dict, Sequence, Tuple

from tools.autonomy import coordinator_orchestrator
from tools.autonomy.coord import CoordinationService, CoordinationServiceError


ROOT = Path(__file__).resolve().parents[2]
TODO_PATH = ROOT / "_plans" / "next-development.todo.json"


def _coord_service() -> CoordinationService:
    return CoordinationService(root=ROOT, todo_path=TODO_PATH)


def _select_work() -> Tuple[dict, Dict[str, Any], Dict[str, Any]]:
    service = _coord_service()
    try:
        return service.select_work()
    except CoordinationServiceError as exc:
        raise SystemExit(str(exc)) from exc


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manager-agent", help="Manager agent id override")
    parser.add_argument("--worker-agent", help="Worker agent id override")
    parser.add_argument("--iterations", type=int, default=1, help="How many items to process (default: 1)")
    parser.add_argument("--sleep", type=float, default=0.0, help="Sleep seconds between iterations")
    parser.add_argument("--dry-run", action="store_true", help="Only print selections without running orchestrator")
    parser.add_argument(
        "--allow-worker-stale",
        action="store_true",
        help="Allow worker session_override when dispatching (passes through to orchestrator)",
    )
    return parser.parse_args(argv)


def _run_once(args: argparse.Namespace) -> int:
    item, plan, step = _select_work()
    plan_id = plan["plan_id"]
    step_id = step["id"]
    print(f"coordinator_loop: selected {item['id']} -> {plan_id}:{step_id}")

    if args.dry_run:
        return 0

    orchestrator_args = [
        "--plan",
        plan_id,
        "--step",
        step_id,
        "--task-id",
        str(item["id"]),
        "--branch",
        f"agent/{args.manager_agent or 'codex-4'}/{plan_id}",
    ]
    if args.manager_agent:
        orchestrator_args.extend(["--manager-agent", args.manager_agent])
    if args.worker_agent:
        orchestrator_args.extend(["--worker-agent", args.worker_agent])
    if args.allow_worker_stale:
        orchestrator_args.append("--allow-worker-stale")
    orchestrator_args.append("--execute")
    return coordinator_orchestrator.main(orchestrator_args)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    iterations = max(1, args.iterations)
    for idx in range(iterations):
        try:
            exit_code = _run_once(args)
        except SystemExit as exc:
            print(f"coordinator_loop: {exc}")
            return exc.code if isinstance(exc.code, int) else 1
        if exit_code != 0:
            return exit_code
        if idx < iterations - 1 and args.sleep > 0:
            time.sleep(args.sleep)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
