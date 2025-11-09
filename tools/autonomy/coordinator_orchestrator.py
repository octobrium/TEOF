"""High-level coordinator orchestrator.

Wraps guard loop and optional task claiming so operators can fire a
single command that enforces manifests, guardrails, and worker
execution. Intended for future autonomous manager agents to call.
"""
from __future__ import annotations

import argparse
from typing import Sequence

from tools.agent import bus_claim, session_guard
from tools.autonomy import coordinator_guard


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, help="Plan id (without .plan.json suffix)")
    parser.add_argument("--step", required=True, help="Plan step id (e.g., step-4)")
    parser.add_argument("--manager-agent", help="Override manager agent id")
    parser.add_argument("--worker-agent", help="Worker agent id (defaults to manager)")
    parser.add_argument("--task-id", help="Optional task id to claim before execution")
    parser.add_argument("--branch", help="Branch to record with the claim")
    parser.add_argument("--allow-worker-stale", action="store_true", help="Allow worker stale session (records override)")
    parser.add_argument("--dry-run", action="store_true", help="Only print planned commands (no guard execution)")
    return parser.parse_args(argv)


def _auto_claim(args: argparse.Namespace, agent_id: str) -> None:
    if not args.task_id:
        return
    claim_args = [
        "claim",
        "--task",
        args.task_id,
        "--agent",
        agent_id,
        "--plan",
        args.plan,
    ]
    if args.branch:
        claim_args.extend(["--branch", args.branch])
    bus_claim.main(claim_args)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    manager_agent = session_guard.resolve_agent_id(args.manager_agent)
    session_guard.ensure_recent_session(manager_agent, context="coordinator_orchestrator")

    _auto_claim(args, manager_agent)

    if args.dry_run:
        print(
            f"orchestrator: would run guard for {args.plan}:{args.step}"
            f" manager={manager_agent} worker={args.worker_agent or manager_agent}"
        )
        return 0

    guard_args = [
        "--plan",
        args.plan,
        "--step",
        args.step,
        "--manager-agent",
        manager_agent,
        "--execute",
    ]
    if args.task_id:
        guard_args.extend(["--task-id", args.task_id])
    if args.worker_agent:
        guard_args.extend(["--worker-agent", args.worker_agent])
    if args.allow_worker_stale:
        guard_args.append("--allow-worker-stale")

    result = coordinator_guard.main(guard_args)
    if result == 0:
        print("orchestrator: guard completed successfully")
    else:
        print(f"orchestrator: guard exited with status {result}")
    return result


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
