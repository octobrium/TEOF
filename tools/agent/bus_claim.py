#!/usr/bin/env python3
"""Manage task claims in the TEOF agent bus."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CLAIMS_DIR = ROOT / "_bus" / "claims"
ASSIGNMENTS_DIR = ROOT / "_bus" / "assignments"
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"


@dataclass
class Claim:
    task_id: str
    agent_id: str
    branch: str
    status: str
    claimed_at: str
    plan_id: str | None = None
    notes: str | None = None
    released_at: str | None = None

    def to_json(self) -> dict[str, Any]:
        data = {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "branch": self.branch,
            "status": self.status,
            "claimed_at": self.claimed_at,
        }
        if self.plan_id:
            data["plan_id"] = self.plan_id
        if self.notes:
            data["notes"] = self.notes
        if self.released_at:
            data["released_at"] = self.released_at
        return data


VALID_STATUS = {"active", "paused", "released", "done"}


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_agent() -> str | None:
    if not MANIFEST_PATH.exists():
        return None
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    agent_id = data.get("agent_id")
    if isinstance(agent_id, str) and agent_id.strip():
        return agent_id.strip()
    return None


def _read_claim(path: Path) -> Claim | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    for field in ("task_id", "agent_id", "branch", "status", "claimed_at"):
        if field not in data:
            raise SystemExit(f"Claim {path} missing field '{field}'")
    return Claim(
        task_id=data["task_id"],
        agent_id=data["agent_id"],
        branch=data["branch"],
        status=data["status"],
        claimed_at=data["claimed"] if "claimed" in data else data["claimed_at"],
        plan_id=data.get("plan_id"),
        notes=data.get("notes"),
        released_at=data.get("released_at"),
    )


def _write_claim(path: Path, claim: Claim) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(claim.to_json(), indent=2, sort_keys=True)
    path.write_text(content + "\n", encoding="utf-8")


def _build_branch(agent_id: str, task_id: str, branch: str | None) -> str:
    if branch:
        return branch
    slug = task_id.lower().replace(" ", "-")
    return f"agent/{agent_id}/{slug}"


def _require_assignment(task_id: str, engineer: str) -> None:
    assign_path = ASSIGNMENTS_DIR / f"{task_id}.json"
    if not assign_path.exists():
        raise SystemExit(
            f"assignment missing for {task_id}; run tools.agent.task_assign first or use --allow-unassigned"
        )
    try:
        data = json.loads(assign_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid assignment JSON {assign_path}: {exc}") from exc
    assignee = data.get("engineer")
    if assignee and assignee != engineer:
        raise SystemExit(
            f"assignment for {task_id} targets {assignee}; update assignment or claim with --allow-unassigned"
        )


def handle_claim(args: argparse.Namespace) -> None:
    agent_id = args.agent or _default_agent()
    if not agent_id:
        raise SystemExit("agent id required (supply --agent or populate AGENT_MANIFEST.json)")
    if args.status not in VALID_STATUS:
        raise SystemExit(f"status must be one of {sorted(VALID_STATUS)}")

    branch = _build_branch(agent_id, args.task, args.branch)
    path = CLAIMS_DIR / f"{args.task}.json"
    existing = _read_claim(path)
    if existing and existing.agent_id != agent_id and existing.status == "active":
        raise SystemExit(
            f"task {args.task} already claimed by {existing.agent_id}; current status={existing.status}"
        )
    if existing is None and not args.allow_unassigned:
        _require_assignment(args.task, agent_id)

    plan_id = args.plan or (existing.plan_id if existing else None)
    clear_notes = bool(getattr(args, "clear_notes", False))
    if args.notes is not None:
        notes = args.notes
    elif clear_notes:
        notes = None
    elif existing:
        notes = existing.notes
    else:
        notes = None

    if existing and args.status not in {"active", "paused"}:
        released_at = existing.released_at
    else:
        released_at = None

    claim = Claim(
        task_id=args.task,
        agent_id=agent_id,
        branch=branch,
        status=args.status,
        claimed_at=_iso_now() if existing is None else existing.claimed_at,
        plan_id=plan_id,
        notes=notes,
        released_at=released_at,
    )
    _write_claim(path, claim)
    print(f"Recorded claim for {args.task} by {agent_id} → {path.relative_to(ROOT)}")


def handle_release(args: argparse.Namespace) -> None:
    path = CLAIMS_DIR / f"{args.task}.json"
    claim = _read_claim(path)
    if not claim:
        raise SystemExit(f"no claim found for task {args.task}")
    agent_id = args.agent or _default_agent() or claim.agent_id
    if claim.agent_id != agent_id:
        raise SystemExit(f"task {args.task} owned by {claim.agent_id}, not {agent_id}")
    status = args.status
    if status not in VALID_STATUS:
        raise SystemExit(f"status must be one of {sorted(VALID_STATUS)}")
    claim.status = status
    claim.released_at = _iso_now()
    if args.notes:
        claim.notes = args.notes
    _write_claim(path, claim)
    print(f"Updated claim {args.task} → status={status}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage agent bus claims")
    sub = parser.add_subparsers(dest="command", required=True)

    claim = sub.add_parser("claim", help="Create or update a task claim")
    claim.add_argument("--task", required=True, help="Task identifier (e.g., QUEUE-001)")
    claim.add_argument("--plan", help="Associated plan id")
    claim.add_argument("--agent", help="Agent id (defaults to AGENT_MANIFEST)")
    claim.add_argument("--branch", help="Working branch name")
    claim.add_argument("--status", default="active", help="Claim status")
    claim.add_argument("--notes", help="Optional notes")
    claim.add_argument(
        "--clear-notes",
        action="store_true",
        help="Clear existing notes when updating a claim",
    )
    claim.add_argument(
        "--allow-unassigned",
        action="store_true",
        help="Bypass assignment requirement (manager override)",
    )
    claim.set_defaults(func=handle_claim)

    release = sub.add_parser("release", help="Release a task claim")
    release.add_argument("--task", required=True, help="Task identifier")
    release.add_argument("--status", default="done", help="New status (done/released/paused)")
    release.add_argument("--agent", help="Agent id (defaults to manifest)")
    release.add_argument("--notes", help="Optional notes to append")
    release.set_defaults(func=handle_release)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except AttributeError:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
