#!/usr/bin/env python3
"""CI guard for planner artifacts."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TERMINAL_CLAIM_STATUSES = {"done", "released", "closed", "cancelled", "abandoned"}

# Ensure repo root is importable when invoked via GitHub Actions (cwd may vary).
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_previous_plan(rel_path: Path) -> dict | None:
    try:
        subprocess.check_call(
            ["git", "rev-parse", "HEAD^"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return None

    try:
        blob = subprocess.check_output(
            ["git", "show", f"HEAD^:{rel_path.as_posix()}"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return None

    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return None


def _as_status_map(data: dict | None) -> tuple[str | None, dict[str, str]]:
    if not isinstance(data, dict):
        return None, {}
    status = data.get("status") if isinstance(data.get("status"), str) else None
    steps = {}
    for step in data.get("steps", []):
        if not isinstance(step, dict):
            continue
        sid = step.get("id")
        st = step.get("status")
        if isinstance(sid, str) and isinstance(st, str):
            steps[sid] = st
    return status, steps


def _check_status_regressions(rel: Path, plan) -> list[str]:
    errors: list[str] = []
    previous = _load_previous_plan(rel)
    prev_status, prev_steps = _as_status_map(previous)

    if prev_status and prev_status == "done" and plan.get("status") != "done":
        errors.append(f"plan status regression done→{plan.get('status')}")

    for step in plan.get("steps", []):
        sid = step.get("id")
        old = prev_steps.get(sid) if sid else None
        if old == "done" and step.get("status") != "done":
            errors.append(f"step {sid} regressed done→{step.get('status')}")

    return errors


def _claim_path(ref: str) -> Path:
    return ROOT / ref


def _check_claim_alignment(rel: Path, plan: dict) -> list[str]:
    errors: list[str] = []
    status = str(plan.get("status", "")).strip().lower()
    if status == "done":
        return errors
    actor = plan.get("actor")
    if not isinstance(actor, str) or not actor.strip():
        return errors
    for link in plan.get("links", []):
        if not isinstance(link, dict):
            continue
        if link.get("type") != "bus":
            continue
        ref = link.get("ref")
        if not isinstance(ref, str) or not ref.startswith("_bus/claims/"):
            continue
        path = _claim_path(ref)
        if not path.exists():
            errors.append(f"plan {plan.get('plan_id')} references missing claim {ref}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid claim JSON {ref}: {exc}")
            continue
        owner = str(data.get("agent_id", "")).strip()
        claim_status = str(data.get("status", "")).strip().lower()
        if claim_status in TERMINAL_CLAIM_STATUSES:
            continue
        if owner != actor:
            errors.append(
                f"plan {plan.get('plan_id')} expects {actor}, but claim {ref} lists {owner or 'UNKNOWN'} (status={claim_status or 'active'})"
            )
    return errors


def main() -> int:
    plans = sorted((ROOT / "_plans").glob("*.plan.json"))
    if not plans:
        print("::error::_plans/ missing *.plan.json files", file=sys.stderr)
        return 1

    from tools.planner.validate import validate_plan

    failures = 0
    for path in plans:
        result = validate_plan(path, strict=True)
        if result.ok:
            plan = result.plan
            if plan is None:
                continue
            rel = path.relative_to(ROOT)
            status_errors = _check_status_regressions(rel, plan)
            claim_errors = _check_claim_alignment(rel, plan)
            if status_errors or claim_errors:
                failures += 1
                print(f"::error::plan invalid {rel}", file=sys.stderr)
                for err in status_errors:
                    print(f"::error::{err}", file=sys.stderr)
                for err in claim_errors:
                    print(f"::error::{err}", file=sys.stderr)
            else:
                print(f"::notice::plan ok {rel}")
        else:
            failures += 1
            print(f"::error::plan invalid {path.relative_to(ROOT)}", file=sys.stderr)
            for err in result.errors:
                print(f"::error::{err}", file=sys.stderr)

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
