#!/usr/bin/env python3
"""Validate plan artifacts stored under `_plans/`."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
PLANS_DIR = ROOT / "_plans"
PLAN_STATUS = {"queued", "in_progress", "blocked", "done"}
STEP_STATUS = PLAN_STATUS
LEGACY_STATUS = {"pending": "queued"}
CHECKPOINT_STATUS = {"pending", "satisfied", "superseded"}

PlanDict = Dict[str, Any]


@dataclass
class ValidationResult:
    path: Path
    errors: List[str]
    plan: PlanDict | None = None

    @property
    def ok(self) -> bool:
        return not self.errors


def _normalize_status(raw: Any, field: str, errors: List[str]) -> str | None:
    if not isinstance(raw, str):
        errors.append(f"{field} must be string")
        return None
    value = LEGACY_STATUS.get(raw.strip().lower(), raw.strip().lower())
    if value not in PLAN_STATUS:
        errors.append(f"{field} must be one of {sorted(PLAN_STATUS)}")
        return None
    return value


def _normalize_step(step: Any, idx: int, errors: List[str]) -> tuple[str | None, Dict[str, Any]]:
    if not isinstance(step, dict):
        errors.append(f"steps[{idx}] must be object")
        return None, {}
    sid = step.get("id")
    if not isinstance(sid, str) or not sid.strip():
        errors.append(f"steps[{idx}].id must be non-empty string")
        sid = None
    title = step.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append(f"steps[{idx}].title must be non-empty string")
    status = _normalize_status(step.get("status", "queued"), f"steps[{idx}].status", errors)
    notes = step.get("notes")
    if notes is not None and not isinstance(notes, str):
        errors.append(f"steps[{idx}].notes must be string when provided")
        notes = None
    receipts_raw = step.get("receipts", [])
    receipts: List[str] = []
    if receipts_raw is None:
        receipts = []
    elif isinstance(receipts_raw, list):
        for ridx, item in enumerate(receipts_raw):
            if not isinstance(item, str) or not item.strip():
                errors.append(f"steps[{idx}].receipts[{ridx}] must be non-empty string")
                continue
            receipts.append(item.strip())
    else:
        errors.append(f"steps[{idx}].receipts must be list when provided")
    return sid, {
        "id": sid,
        "title": title.strip() if isinstance(title, str) else title,
        "status": status,
        "notes": notes.strip() if isinstance(notes, str) and notes.strip() else None,
        "receipts": receipts,
    }


def _validate_checkpoint(raw: Any, errors: List[str]) -> Dict[str, Any] | None:
    if not isinstance(raw, dict):
        errors.append("checkpoint must be object")
        return None
    description = raw.get("description")
    owner = raw.get("owner")
    status = raw.get("status")
    ok = True
    if not isinstance(description, str) or not description.strip():
        errors.append("checkpoint.description must be non-empty string")
        ok = False
    if not isinstance(owner, str) or not owner.strip():
        errors.append("checkpoint.owner must be non-empty string")
        ok = False
    if status not in CHECKPOINT_STATUS:
        errors.append(f"checkpoint.status must be one of {sorted(CHECKPOINT_STATUS)}")
        ok = False
    if not ok:
        return None
    return {
        "description": description.strip(),
        "owner": owner.strip(),
        "status": status,
    }


def _load_plan(data: Any, path: Path) -> Tuple[PlanDict | None, List[str]]:
    errors: List[str] = []
    if not isinstance(data, dict):
        return None, ["plan must be a JSON object"]

    version = data.get("version")
    if not isinstance(version, int) or version < 0:
        errors.append("version must be non-negative int")
    plan_id = data.get("plan_id")
    if not isinstance(plan_id, str) or not plan_id.strip():
        errors.append("plan_id must be non-empty string")
        plan_id = None
    else:
        expected = f"{plan_id.strip()}.plan.json"
        if path.name != expected:
            errors.append(f"file name must match plan_id (+.plan.json); expected '{expected}'")
        if not re.match(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$", plan_id.strip()):
            errors.append("plan_id must follow YYYY-MM-DD-slug format")
        plan_id = plan_id.strip()

    created = data.get("created")
    try:
        created_norm = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ") if isinstance(created, str) else None
    except ValueError:
        created_norm = None
    if created_norm is None:
        errors.append("created must be ISO8601 UTC string")

    actor = data.get("actor")
    if not isinstance(actor, str) or not actor.strip():
        errors.append("actor must be non-empty string")
    summary = data.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        errors.append("summary must be non-empty string")

    status = _normalize_status(data.get("status", "queued"), "status", errors)

    raw_steps = data.get("steps")
    steps: List[Dict[str, Any]] = []
    if not isinstance(raw_steps, list) or not raw_steps:
        errors.append("steps must be a non-empty list")
    else:
        seen: set[str] = set()
        in_progress = 0
        for idx, raw_step in enumerate(raw_steps):
            sid, normalized = _normalize_step(raw_step, idx, errors)
            if sid and sid in seen:
                errors.append(f"steps[{idx}].id duplicates '{sid}'")
            if normalized.get("status") == "in_progress":
                in_progress += 1
            if sid:
                seen.add(sid)
            steps.append(normalized)
        if in_progress > 1:
            errors.append("only one step may be in_progress at a time")
        if not any(step.get("id") for step in steps):
            errors.append("steps must include at least one valid entry")

    checkpoint = _validate_checkpoint(data.get("checkpoint"), errors)

    receipts_raw = data.get("receipts")
    receipts: List[str] = []
    if receipts_raw is None:
        receipts = []
    elif isinstance(receipts_raw, list):
        for idx, item in enumerate(receipts_raw):
            if not isinstance(item, str) or not item.strip():
                errors.append(f"receipts[{idx}] must be non-empty string")
                continue
            receipts.append(item.strip())
    else:
        errors.append("receipts must be list when provided")

    links_raw = data.get("links")
    links: List[Dict[str, str]] = []
    if links_raw is None:
        links = []
    elif isinstance(links_raw, list):
        for idx, item in enumerate(links_raw):
            if not isinstance(item, dict):
                errors.append(f"links[{idx}] must be object")
                continue
            typ = item.get("type")
            ref = item.get("ref")
            if not isinstance(typ, str) or not isinstance(ref, str):
                errors.append(f"links[{idx}] must include string type/ref")
                continue
            links.append({"type": typ, "ref": ref})
    else:
        errors.append("links must be list when provided")

    if errors:
        return None, errors

    return (
        {
            "version": version,
            "plan_id": plan_id,
            "created": created_norm,
            "actor": actor.strip(),
            "summary": summary.strip(),
            "status": status,
            "steps": steps,
            "checkpoint": checkpoint,
            "receipts": receipts,
            "links": links,
            "path": path,
        },
        [],
    )


def _check_receipt(path_str: str, context: str, repo_root: Path, errors: List[str]) -> None:
    if "://" in path_str:
        return
    rec_path = Path(path_str)
    if rec_path.is_absolute():
        errors.append(f"{context} must be relative path, got absolute '{path_str}'")
        return
    if any(part == ".." for part in rec_path.parts):
        errors.append(f"{context} may not contain '..' segments")
        return
    target = repo_root / rec_path
    if not target.exists():
        errors.append(f"{context} does not exist at '{path_str}'")
        return
    if target.suffix.lower() == ".json":
        try:
            json.loads(target.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            errors.append(f"{context} must be UTF-8 text: '{path_str}'")
        except json.JSONDecodeError:
            errors.append(f"{context} must be valid JSON: '{path_str}'")


def strict_checks(plan: PlanDict, *, repo_root: Path) -> List[str]:
    errors: List[str] = []
    if plan["checkpoint"]["status"] == "satisfied" and not plan["receipts"]:
        errors.append("checkpoint.status=satisfied requires at least one receipt")

    seen_plan: set[str] = set()
    for idx, entry in enumerate(plan["receipts"]):
        if entry in seen_plan:
            errors.append(f"receipts[{idx}] duplicates '{entry}'")
            continue
        seen_plan.add(entry)
        _check_receipt(entry, f"receipts[{idx}]", repo_root, errors)

    seen_steps: set[str] = set()
    for sidx, step in enumerate(plan["steps"]):
        for ridx, entry in enumerate(step["receipts"]):
            if entry in seen_steps:
                errors.append(f"steps[{sidx}].receipts[{ridx}] duplicates '{entry}'")
                continue
            seen_steps.add(entry)
            _check_receipt(entry, f"steps[{sidx}].receipts[{ridx}]", repo_root, errors)
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate planner artifacts")
    parser.add_argument("paths", nargs="*", help="Optional plan file paths; defaults to all *.plan.json under _plans/")
    parser.add_argument("--strict", action="store_true", help="Enforce repository-coupled invariants (e.g., receipt existence)")
    return parser.parse_args()


def iter_plan_paths(paths: Iterable[str]) -> List[Path]:
    if paths:
        return [Path(p).resolve() for p in paths]
    return sorted(PLANS_DIR.glob("*.plan.json"))


def validate_plan(path: Path, *, strict: bool = False) -> ValidationResult:
    errors: List[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return ValidationResult(path, ["file not found"])
    except json.JSONDecodeError as exc:
        return ValidationResult(path, [f"invalid JSON: {exc}"])

    plan, structural_errors = _load_plan(data, path)
    errors.extend(structural_errors)
    if plan and strict:
        errors.extend(strict_checks(plan, repo_root=ROOT))
    if errors:
        return ValidationResult(path, errors)
    return ValidationResult(path, errors, plan)


def main() -> int:
    args = parse_args()
    plan_paths = iter_plan_paths(args.paths)
    if not plan_paths:
        print("no plan files found", file=sys.stderr)
        return 1

    failures = 0
    for path in plan_paths:
        result = validate_plan(path, strict=args.strict)
        rel = path.relative_to(ROOT)
        if result.ok:
            print(f"OK {rel}")
        else:
            failures += 1
            print(f"FAIL {rel}", file=sys.stderr)
            for err in result.errors:
                print(f"  - {err}", file=sys.stderr)

    return 0 if failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
