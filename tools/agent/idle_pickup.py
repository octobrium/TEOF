#!/usr/bin/env python3
"""Idle pickup helper for agents.

Lists unclaimed tasks and optionally claims one automatically.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

from tools.agent import task_assign, bus_claim

ROOT = Path(__file__).resolve().parents[2]
ASSIGNMENTS_DIR = ROOT / "_bus" / "assignments"
CLAIMS_DIR = ROOT / "_bus" / "claims"
QUEUE_DIR = ROOT / "queue"
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"


@dataclass
class Assignment:
    task_id: str
    engineer: Optional[str]
    manager: Optional[str]
    plan_id: Optional[str]
    branch: Optional[str]
    status: Optional[str]
    path: Path


@dataclass
class Claim:
    task_id: str
    agent_id: str
    status: str
    path: Path


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


def _load_assignments() -> dict[str, Assignment]:
    assignments: dict[str, Assignment] = {}
    if not ASSIGNMENTS_DIR.exists():
        return assignments
    for path in sorted(ASSIGNMENTS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        assignments[path.stem] = Assignment(
            task_id=path.stem,
            engineer=data.get("engineer"),
            manager=data.get("manager"),
            plan_id=data.get("plan_id"),
            branch=data.get("branch"),
            status=data.get("status"),
            path=path,
        )
    return assignments


def _load_claims() -> dict[str, Claim]:
    claims: dict[str, Claim] = {}
    if not CLAIMS_DIR.exists():
        return claims
    for path in sorted(CLAIMS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        task_id = data.get("task_id")
        agent_id = data.get("agent_id")
        status = data.get("status")
        if not task_id or not agent_id or not status:
            continue
        claims[task_id] = Claim(task_id=task_id, agent_id=agent_id, status=status, path=path)
    return claims


def _queue_summary(task_id: str) -> str:
    path = QUEUE_DIR / f"{task_id.lower()}.md"
    if not path.exists():
        return "(no queue entry)"
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                return line
    except OSError:
        pass
    return "(no summary)"


def list_candidates(agent: Optional[str] = None) -> list[dict[str, Any]]:
    assignments = _load_assignments()
    claims = _load_claims()
    results: list[dict[str, Any]] = []
    for task_id, assignment in assignments.items():
        claim = claims.get(task_id)
        status = assignment.status or "unassigned"
        if claim and claim.status == "active":
            continue
        # Candidate if unassigned or assigned to agent without active claim
        if assignment.engineer:
            if agent and assignment.engineer != agent:
                continue
            # Only surface when not actively claimed
            results.append(
                {
                    "task": task_id,
                    "assigned_to": assignment.engineer,
                    "plan": assignment.plan_id,
                    "branch": assignment.branch,
                    "status": status,
                    "summary": _queue_summary(task_id),
                    "claimed": bool(claim),
                }
            )
        else:
            results.append(
                {
                    "task": task_id,
                    "assigned_to": None,
                    "plan": assignment.plan_id,
                    "branch": assignment.branch,
                    "status": status,
                    "summary": _queue_summary(task_id),
                    "claimed": False,
                }
            )
    # Also show queue entries without assignments (pure backlog)
    for path in sorted(QUEUE_DIR.glob("*.md")):
        task_id = path.stem.upper()
        if task_id in assignments:
            continue
        results.append(
            {
                "task": task_id,
                "assigned_to": None,
                "plan": None,
                "branch": None,
                "status": "unassigned",
                "summary": _queue_summary(task_id),
                "claimed": False,
            }
        )
    return results


def claim_task(task_id: str, agent: str, manager: Optional[str] = None) -> None:
    assignments = _load_assignments()
    assignment = assignments.get(task_id)
    claims = _load_claims()
    claim = claims.get(task_id)
    if claim and claim.status == "active":
        raise SystemExit(f"task {task_id} already claimed by {claim.agent_id}")

    if assignment is None or not assignment.engineer:
        # create assignment to this agent (auto-claim handles claim creation)
        args = [
            "--task",
            task_id,
            "--engineer",
            agent,
        ]
        if manager:
            args.extend(["--manager", manager])
        if assignment and assignment.plan_id:
            args.extend(["--plan", assignment.plan_id])
        if assignment and assignment.branch:
            args.extend(["--branch", assignment.branch])
        task_assign.main(args)
        return

    if assignment.engineer != agent:
        raise SystemExit(
            f"task {task_id} assigned to {assignment.engineer}; unable to claim for {agent}."
        )

    claim_args = [
        "claim",
        "--task",
        task_id,
        "--agent",
        agent,
    ]
    if assignment.plan_id:
        claim_args.extend(["--plan", assignment.plan_id])
    if assignment.branch:
        claim_args.extend(["--branch", assignment.branch])
    bus_claim.main(claim_args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Suggest or claim tasks for idle agents")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="List available tasks")
    list_parser.add_argument("--agent", help="Filter for a specific agent id")
    list_parser.set_defaults(func=cmd_list)

    claim_parser = sub.add_parser("claim", help="Claim a task (auto-assign if needed)")
    claim_parser.add_argument("--task", required=True, help="Task identifier (e.g., QUEUE-001)")
    claim_parser.add_argument("--agent", help="Agent id (defaults to manifest)")
    claim_parser.add_argument("--manager", help="Manager id to record on assignment when auto-assigning")
    claim_parser.set_defaults(func=cmd_claim)

    return parser


def cmd_list(args: argparse.Namespace) -> int:
    agent = args.agent
    candidates = list_candidates(agent)
    if not candidates:
        print("No available tasks.")
        return 0
    for entry in candidates:
        assignee = entry["assigned_to"] or "(unassigned)"
        status = entry["status"]
        claimed = "yes" if entry["claimed"] else "no"
        summary = entry["summary"]
        plan = entry["plan"] or "-"
        print(f"{entry['task']}: assigned_to={assignee} status={status} claimed={claimed} plan={plan}")
        print(f"    {summary}")
    return 0


def cmd_claim(args: argparse.Namespace) -> int:
    agent = args.agent or _load_manifest_agent()
    if not agent:
        raise SystemExit("agent id missing; provide --agent or populate AGENT_MANIFEST.json")
    claim_task(args.task, agent, manager=args.manager)
    print(f"Claimed {args.task} for {agent}")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
