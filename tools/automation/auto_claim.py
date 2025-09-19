#!/usr/bin/env python3
"""Auto-claim queued plans for idle agents.

The script scans `_plans/*.plan.json`, locates plans owned by known agents with
status `queued`/`pending`, and ensures each has an active claim in
`_bus/claims/`. When run with `--execute`, it writes/updates the claim JSON and
marks the plan `status` as `in_progress`. By default (dry-run) it only prints
what would change.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional
import re

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path(os.environ.get("TEOF_ROOT", DEFAULT_ROOT))
PLANS_DIR = ROOT / "_plans"
CLAIMS_DIR = ROOT / "_bus" / "claims"

AUTO_AGENTS = {"codex-1", "codex-2", "codex-3", "codex-4"}
ACTIVE_STATUSES = {"active", "paused"}
QUEUED_STATUSES = {"queued", "pending"}


@dataclass
class Candidate:
    agent: str
    plan_id: str
    plan_path: Path
    task_id: str
    claim_path: Path
    branch: str
    plan_data: dict
    existing_claim: Optional[dict]


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iter_plan_paths() -> Iterable[Path]:
    if not PLANS_DIR.exists():
        return []
    return sorted(PLANS_DIR.glob("*.plan.json"))


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def parse_task_id(plan: dict) -> Optional[str]:
    links = plan.get("links", [])
    for link in links:
        ref = link.get("ref", "")
        if ref.startswith("queue/"):
            # Expect pattern like queue/012-example.md
            match = re.search(r"/(\d+)-", ref)
            if match:
                number = match.group(1)
                return f"QUEUE-{number.zfill(3)}"
        if "#APOP-" in ref:
            anchor = ref.split("#", 1)[1]
            if anchor.startswith("APOP-"):
                return anchor
    return None


def load_claim(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid claim JSON in {path}: {exc}") from exc
    return data


def build_branch(agent: str, task_id: str) -> str:
    slug = task_id.lower().replace(" ", "-")
    return f"agent/{agent}/{slug}"


def gather_candidates() -> list[Candidate]:
    candidates: list[Candidate] = []
    for plan_path in iter_plan_paths():
        plan = load_json(plan_path)
        status = (plan.get("status") or "").lower()
        if status not in QUEUED_STATUSES:
            continue
        agent = plan.get("actor")
        if not agent or agent.lower() not in AUTO_AGENTS:
            continue
        task_id = parse_task_id(plan)
        if not task_id:
            continue
        claim_path = CLAIMS_DIR / f"{task_id}.json"
        existing = load_claim(claim_path)
        if existing:
            claim_status = (existing.get("status") or "").lower()
            if claim_status in ACTIVE_STATUSES and existing.get("agent_id") == agent:
                # already active for this agent
                continue
        branch = build_branch(agent, task_id)
        candidates.append(
            Candidate(
                agent=agent,
                plan_id=plan.get("plan_id", plan_path.stem),
                plan_path=plan_path,
                task_id=task_id,
                claim_path=claim_path,
                branch=branch,
                plan_data=plan,
                existing_claim=existing,
            )
        )
    return candidates


def write_claim(candidate: Candidate) -> None:
    candidate.claim_path.parent.mkdir(parents=True, exist_ok=True)
    if candidate.existing_claim:
        claimed_at = candidate.existing_claim.get("claimed_at") or iso_now()
        notes = candidate.existing_claim.get("notes")
    else:
        claimed_at = iso_now()
        notes = None
    payload = {
        "task_id": candidate.task_id,
        "agent_id": candidate.agent,
        "branch": candidate.branch,
        "status": "active",
        "claimed_at": claimed_at,
        "plan_id": candidate.plan_id,
    }
    if notes:
        payload["notes"] = notes
    candidate.claim_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def update_plan_status(candidate: Candidate) -> None:
    data = candidate.plan_data
    data["status"] = "in_progress"
    candidate.plan_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_summary(candidate: Candidate) -> str:
    status = candidate.plan_data.get("status")
    return (
        f"{candidate.plan_id}: claim {candidate.task_id} for {candidate.agent}"
        f" (plan_status={status})"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Apply changes (default is dry-run)",
    )
    parser.add_argument(
        "--agents",
        nargs="*",
        help="Restrict automation to these agents (defaults to codex-1..4)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.agents:
        selected = {agent.lower() for agent in args.agents}
    else:
        selected = AUTO_AGENTS

    candidates = [cand for cand in gather_candidates() if cand.agent.lower() in selected]

    if not candidates:
        print("No plans require auto-claim.")
        return 0

    action = "APPLY" if args.execute else "DRY-RUN"
    print(f"auto-claim ({action}): {len(candidates)} candidate(s)")
    for candidate in candidates:
        print(" -", render_summary(candidate))

    if not args.execute:
        print("Re-run with --execute to create claims.")
        return 0

    for candidate in candidates:
        write_claim(candidate)
        update_plan_status(candidate)
        print(
            f"claimed {candidate.task_id} for {candidate.agent} → {candidate.claim_path.relative_to(ROOT)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
