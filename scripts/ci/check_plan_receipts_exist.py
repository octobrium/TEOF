#!/usr/bin/env python3
"""
Advisory check: verify plan receipts exist and, when required, are tracked by git.

Non-blocking by design (exit 0). Prints WARN lines for:
  - Missing receipt files referenced by plan or steps
  - Files that must be tracked (non `_report/` paths) but aren't
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.planner import validate as planner_validate


ROOT = Path(__file__).resolve().parents[2]
OPTIONAL_TRACKING_PREFIXES = planner_validate.RECEIPT_TRACKING_OPTIONAL_PREFIXES


def _tracking_required(rel: Path) -> bool:
    rel_posix = rel.as_posix()
    return not any(rel_posix.startswith(prefix) for prefix in OPTIONAL_TRACKING_PREFIXES)


def _git_tracked(rel_path: Path) -> bool:
    try:
        subprocess.check_call(
            ["git", "ls-files", "--error-unmatch", rel_path.as_posix()],
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def main() -> int:
    plans_dir = ROOT / "_plans"
    if not plans_dir.exists():
        print("WARN: _plans directory missing; skipping plan receipts existence check")
        return 0

    plan_files = sorted(plans_dir.glob("*.plan.json"))
    if not plan_files:
        print("WARN: no plans found under _plans; skipping plan receipts existence check")
        return 0

    warnings = 0

    for plan_path in plan_files:
        try:
            data = json.loads(plan_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"WARN: invalid JSON {plan_path.relative_to(ROOT)}: {exc}")
            warnings += 1
            continue

        def check_receipt(rel_str: str, context: str) -> None:
            nonlocal warnings
            if not isinstance(rel_str, str) or not rel_str.strip():
                return
            if "://" in rel_str:
                return
            rel = Path(rel_str)
            abs_path = (ROOT / rel).resolve()
            if not abs_path.exists():
                print(f"WARN: missing receipt {rel} (context={context})")
                warnings += 1
            elif _tracking_required(rel) and not _git_tracked(rel):
                print(f"WARN: untracked receipt {rel} (context={context})")
                warnings += 1

        for r in data.get("receipts", []) or []:
            check_receipt(r, f"plan:{data.get('plan_id')}")

        for step in data.get("steps", []) or []:
            if not isinstance(step, dict):
                continue
            sid = step.get("id")
            for r in step.get("receipts", []) or []:
                check_receipt(r, f"step:{sid}")

    if warnings == 0:
        print("OK: plan receipts sanity (exist + tracked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
