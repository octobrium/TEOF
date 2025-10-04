#!/usr/bin/env python3
"""Surface active assignments for an agent and verify required plan artifacts exist."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

ROOT = Path(__file__).resolve().parents[2]
CLAIMS_DIR = ROOT / "_bus" / "claims"
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"
PLANS_DIR = ROOT / "_plans"
TERMINAL_STATUSES = {"done", "released", "closed", "cancelled", "abandoned"}


@dataclass
class Assignment:
    task_id: str
    plan_id: Optional[str]
    status: str
    claim_path: Path

    @property
    def plan_path(self) -> Optional[Path]:
        if not self.plan_id:
            return None
        return PLANS_DIR / f"{self.plan_id}.plan.json"

    @property
    def is_active(self) -> bool:
        return self.status.lower() not in TERMINAL_STATUSES


def _manifest_agent() -> Optional[str]:
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


def _iter_assignments(agent: str) -> Iterable[Assignment]:
    if not CLAIMS_DIR.exists():
        return []
    for path in CLAIMS_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if data.get("agent_id") != agent:
            continue
        yield Assignment(
            task_id=str(data.get("task_id", "")),
            plan_id=data.get("plan_id"),
            status=str(data.get("status", "")),
            claim_path=path,
        )


def run_check(agent: str) -> tuple[bool, list[dict[str, str]]]:
    missing: list[dict[str, str]] = []
    for assignment in _iter_assignments(agent):
        if not assignment.is_active:
            continue
        plan_path = assignment.plan_path
        if plan_path and plan_path.exists():
            continue
        if plan_path is None:
            missing.append(
                {
                    "task_id": assignment.task_id,
                    "issue": "missing_plan_id",
                    "claim": str(assignment.claim_path.relative_to(ROOT)),
                }
            )
        else:
            missing.append(
                {
                    "task_id": assignment.task_id,
                    "plan_id": assignment.plan_id or "",
                    "issue": "plan_missing",
                    "expected_plan": str(plan_path.relative_to(ROOT)),
                }
            )
    return len(missing) == 0, missing


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="List active assignments and flag missing plan artifacts")
    parser.add_argument("--agent", help="Agent id (defaults to AGENT_MANIFEST.json)")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    agent = args.agent or _manifest_agent()
    if not agent:
        parser.error("Agent id not provided and AGENT_MANIFEST.json missing")

    ok, missing = run_check(agent)

    if args.json:
        payload = {"agent": agent, "ok": ok, "missing": missing}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        active = [a for a in _iter_assignments(agent) if a.is_active]
        if not active:
            print(f"No active assignments for {agent}.")
        else:
            print(f"Active assignments for {agent}:")
            for entry in active:
                plan = entry.plan_path
                status = "missing" if plan is None or not plan.exists() else "present"
                plan_str = plan.relative_to(ROOT) if plan else "<none>"
                print(f"  - {entry.task_id}: plan={plan_str} [{status}]")
        if missing:
            print("\nIssues detected:")
            for item in missing:
                details = ", ".join(f"{k}={v}" for k, v in item.items() if k != "issue")
                print(f"  - {item['issue']}: {details}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
