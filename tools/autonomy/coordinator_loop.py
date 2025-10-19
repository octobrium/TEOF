"""Coordinator loop that picks backlog items and runs orchestrator."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Sequence, Tuple

from tools.autonomy import coordinator_orchestrator
from tools.autonomy.shared import load_json


ROOT = Path(__file__).resolve().parents[2]
TODO_PATH = ROOT / "_plans" / "next-development.todo.json"


def _iter_pending_items(todo: Dict[str, Any]) -> Iterable[dict]:
    for item in todo.get("items", []):
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "")).lower()
        if status in {"pending", "queued", "in_progress"}:
            yield item


def _plan_step(plan_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    plan_path = ROOT / "_plans" / f"{plan_id}.plan.json"
    data = load_json(plan_path)
    if not isinstance(data, dict):
        raise SystemExit(f"::error:: plan {plan_id} not found or invalid")
    for step in data.get("steps", []):
        if isinstance(step, dict) and step.get("status") != "done":
            return data, step
    raise SystemExit(f"::error:: plan {plan_id} has no pending steps")


def _select_work() -> Tuple[dict, Dict[str, Any], Dict[str, Any]]:
    todo = load_json(TODO_PATH)
    if not isinstance(todo, dict):
        raise SystemExit("::error:: next-development.todo.json missing or invalid")
    for item in _iter_pending_items(todo):
        plan_id = item.get("plan_suggestion")
        if not isinstance(plan_id, str) or not plan_id:
            continue
        try:
            plan, step = _plan_step(plan_id)
        except SystemExit:
            continue
        return item, plan, step
    raise SystemExit("::error:: no pending todo items with actionable plans")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manager-agent", help="Manager agent id override")
    parser.add_argument("--worker-agent", help="Worker agent id override")
    parser.add_argument("--iterations", type=int, default=1, help="How many items to process (default: 1)")
    parser.add_argument("--sleep", type=float, default=0.0, help="Sleep seconds between iterations")
    parser.add_argument("--dry-run", action="store_true", help="Only print selections without running orchestrator")
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
