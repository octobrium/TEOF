#!/usr/bin/env python3
"""Append a memory log entry referencing a planner artifact."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from tools.planner.validate import validate_plan

ROOT = Path(__file__).resolve().parents[2]
MEMORY_LOG = ROOT / "memory" / "log.jsonl"


def build_entry(plan_result) -> dict:
    plan = plan_result.plan
    timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    receipts = set(plan.get("receipts", []))
    for step in plan.get("steps", []):
        receipts.update(step.get("receipts", []))
    artifacts = [str(plan["path"].relative_to(ROOT))]
    artifacts.extend(sorted(receipts))
    plan_id = plan.get("plan_id")
    summary = plan.get("summary")
    return {
        "ts": timestamp,
        "actor": plan.get("actor"),
        "summary": f"Plan update {plan_id}: {summary}",
        "ref": f"plan:{plan_id}",
        "artifacts": artifacts,
        "signatures": [],
    }


def append_memory(entry: dict) -> None:
    MEMORY_LOG.parent.mkdir(parents=True, exist_ok=True)
    with MEMORY_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Link a plan to the memory log")
    parser.add_argument("plan", help="Path to the plan json file")
    args = parser.parse_args()

    plan_path = Path(args.plan).resolve()
    result = validate_plan(plan_path, strict=True)
    if not result.ok or result.plan is None:
        msg = "; ".join(result.errors) if result.errors else "plan validation failed"
        parser.error(msg)

    entry = build_entry(result)
    append_memory(entry)
    print(MEMORY_LOG)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
