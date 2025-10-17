#!/usr/bin/env python3
"""Validate plan artifacts stored under `_plans/`."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from tools.fractal import conformance as fractal_conformance
from tools.planner.systemic_targets import (
    normalize_axis,
    sort_axes,
)

ROOT = Path(__file__).resolve().parents[2]
PLANS_DIR = ROOT / "_plans"
PLAN_STATUS = {"queued", "in_progress", "blocked", "done"}
STEP_STATUS = PLAN_STATUS
LEGACY_STATUS = {"pending": "queued"}
CHECKPOINT_STATUS = {"pending", "satisfied", "superseded"}
VALID_LAYERS = {f"L{idx}" for idx in range(7)}
SYSTEMIC_MIN, SYSTEMIC_MAX = 1, 10

PlanDict = Dict[str, Any]


DEFAULT_SUMMARY_DIR = ROOT / "_report" / "planner" / "validate"

_QUEUE_INDEX: Dict[str, fractal_conformance.QueueEntry] | None = None


def _dedupe_preserve(items: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    ordered: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _get_queue_index() -> Dict[str, fractal_conformance.QueueEntry]:
    global _QUEUE_INDEX
    if _QUEUE_INDEX is None:
        _QUEUE_INDEX = fractal_conformance.gather_queue_entries()
    return _QUEUE_INDEX


def _parse_coordinate_token(token: str) -> tuple[Optional[int], Optional[str]]:
    token = token.strip()
    if not token or ":" not in token:
        return None, None
    left, right = token.split(":", 1)
    systemic: Optional[int] = None
    layer: Optional[str] = None
    left = left.strip()
    if left.upper().startswith("S"):
        try:
            systemic = int(left[1:])
        except ValueError:
            systemic = None
    right = right.strip().upper()
    if right.startswith("L") and len(right) >= 2:
        layer = right[:2]
    return systemic, layer


def _extract_coordinate_pairs(entry: fractal_conformance.QueueEntry) -> list[tuple[Optional[int], Optional[str]]]:
    pairs: list[tuple[Optional[int], Optional[str]]] = []
    for coord in entry.coordinates:
        pairs.append(_parse_coordinate_token(coord))
    return pairs


def _detect_queue_warnings(
    plan: PlanDict,
    queue_index: Dict[str, fractal_conformance.QueueEntry],
) -> List[Dict[str, Any]]:
    warnings: List[Dict[str, Any]] = []
    plan_id = plan.get("plan_id") or str(plan.get("path"))
    plan_layer = plan.get("layer")
    plan_systemic = plan.get("systemic_scale")
    plan_systemic_targets = [
        token
        for token in plan.get("systemic_targets") or []
        if isinstance(token, str) and token.strip().upper().startswith("S")
    ]
    links = plan.get("links") or []
    for link in links:
        if not isinstance(link, dict) or link.get("type") != "queue":
            continue
        ref = link.get("ref")
        if not isinstance(ref, str) or not ref:
            continue
        entry = queue_index.get(ref)
        if entry is None:
            warnings.append(
                {
                    "plan_id": plan_id,
                    "queue_ref": ref,
                    "issue": "missing_queue_entry",
                    "message": f"{plan_id}: queue entry '{ref}' not found",
                }
            )
            continue

        coordinate_pairs = _extract_coordinate_pairs(entry)
        systemic_candidates = [pair[0] for pair in coordinate_pairs if pair[0] is not None]
        layer_candidates = [pair[1] for pair in coordinate_pairs if pair[1]]

        if (
            systemic_candidates
            and isinstance(plan_systemic, int)
            and plan_systemic not in systemic_candidates
        ):
            warnings.append(
                {
                    "plan_id": plan_id,
                    "queue_ref": ref,
                    "issue": "systemic_mismatch",
                    "expected": systemic_candidates,
                    "actual": plan_systemic,
                    "message": (
                        f"{plan_id}: systemic_scale {plan_systemic} not in queue {ref}"
                    ),
                }
            )

        if layer_candidates and isinstance(plan_layer, str) and plan_layer not in layer_candidates:
            warnings.append(
                {
                    "plan_id": plan_id,
                    "queue_ref": ref,
                    "issue": "layer_mismatch",
                    "expected": layer_candidates,
                    "actual": plan_layer,
                    "message": (
                        f"{plan_id}: layer {plan_layer} not in queue {ref}"
                    ),
                }
            )

        if entry.systemic_targets:
            normalized_plan_targets = {token.strip().upper() for token in plan_systemic_targets}
            expected_targets = {token.strip().upper() for token in entry.systemic_targets}
            if not normalized_plan_targets:
                warnings.append(
                    {
                        "plan_id": plan_id,
                        "queue_ref": ref,
                        "issue": "missing_systemic_targets",
                        "expected": sorted(expected_targets),
                        "message": (
                            f"{plan_id}: queue {ref} declares systemic targets "
                            f"{sorted(expected_targets)} but plan lacks systemic_targets"
                        ),
                    }
                )
            else:
                missing = sorted(expected_targets - normalized_plan_targets)
                if missing:
                    warnings.append(
                        {
                            "plan_id": plan_id,
                            "queue_ref": ref,
                            "issue": "systemic_targets_mismatch",
                            "expected": sorted(expected_targets),
                            "actual": sorted(normalized_plan_targets),
                            "missing": missing,
                            "message": (
                                f"{plan_id}: systemic_targets mismatch for queue {ref}; "
                                f"expected {sorted(expected_targets)}, got {sorted(normalized_plan_targets)}"
                            ),
                        }
                    )

    return warnings


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

    raw_layer = data.get("layer")
    layer = None
    if not isinstance(raw_layer, str) or raw_layer.strip() not in VALID_LAYERS:
        errors.append("layer must be one of L0-L6")
    else:
        layer = raw_layer.strip()

    raw_systemic_scale = data.get("systemic_scale")
    systemic_scale = None
    if not isinstance(raw_systemic_scale, int):
        errors.append("systemic_scale must be integer")
    elif not (SYSTEMIC_MIN <= raw_systemic_scale <= SYSTEMIC_MAX):
        errors.append(
            f"systemic_scale must be between {SYSTEMIC_MIN} and {SYSTEMIC_MAX}"
        )
    else:
        systemic_scale = raw_systemic_scale

    raw_systemic_targets = data.get("systemic_targets")
    systemic_targets: List[str] = []
    if isinstance(raw_systemic_targets, list):
        if not raw_systemic_targets:
            errors.append("systemic_targets must include at least one axis")
        else:
            for idx, token in enumerate(raw_systemic_targets):
                if not isinstance(token, str):
                    errors.append(f"systemic_targets[{idx}] must be string")
                    continue
                normalized = normalize_axis(token)
                if not normalized:
                    errors.append(f"systemic_targets[{idx}] must be S1-S10 token")
                    continue
                systemic_targets.append(normalized)
            systemic_targets = sort_axes(systemic_targets)
    else:
        errors.append("systemic_targets must be list of S# tokens")

    raw_layer_targets = data.get("layer_targets")
    layer_targets: List[str] = []
    if raw_layer_targets is None:
        if layer:
            layer_targets = [layer]
    elif isinstance(raw_layer_targets, list):
        collected: List[str] = []
        for idx, token in enumerate(raw_layer_targets):
            if not isinstance(token, str):
                errors.append(f"layer_targets[{idx}] must be string")
                continue
            normalized = token.strip().upper()
            if normalized not in VALID_LAYERS:
                errors.append(f"layer_targets[{idx}] must be one of L0-L6")
                continue
            collected.append(normalized)
        if layer:
            collected.insert(0, layer)
        layer_targets = _dedupe_preserve(collected)
    else:
        errors.append("layer_targets must be list when provided")

    if "legacy_loop_target" in data:
        errors.append("legacy_loop_target is deprecated; use systemic_targets/layer_targets")

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
            "layer": layer,
            "systemic_scale": systemic_scale,
            "systemic_targets": systemic_targets,
            "layer_targets": layer_targets,
        },
        [],
    )


@lru_cache(maxsize=None)
def _git_tracked_paths(repo_root: str) -> Optional[set[str]]:
    """Return the set of git-tracked paths for `repo_root`, or None if unavailable."""
    try:
        output = subprocess.check_output(
            ["git", "-C", repo_root, "ls-files"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None
    entries = {line.strip() for line in output.splitlines() if line.strip()}
    return entries


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
    tracked = _git_tracked_paths(str(repo_root))
    if tracked is not None:
        normalized = rec_path.as_posix()
        if normalized not in tracked:
            errors.append(f"{context} is not tracked by git: '{path_str}'")


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
    parser.add_argument("--output", help="Write JSON summary to this path")
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


def _relative_to_root(path: Path) -> Path:
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path.resolve()


def _default_summary_path() -> Path:
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    DEFAULT_SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_SUMMARY_DIR / f"summary-{stamp}.json"


def _write_summary(results: List[Dict[str, Any]], *, output: Path, strict: bool, exit_code: int) -> None:
    payload = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "strict": strict,
        "exit_code": exit_code,
        "plans": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    plan_paths = iter_plan_paths(args.paths)
    if not plan_paths:
        print("no plan files found", file=sys.stderr)
        return 1

    queue_index = _get_queue_index()

    results: List[Dict[str, Any]] = []
    failures = 0
    for path in plan_paths:
        result = validate_plan(path, strict=args.strict)
        rel = _relative_to_root(path)
        rel_str = str(rel)
        entry: Dict[str, Any] = {"path": rel_str, "ok": result.ok, "errors": list(result.errors)}
        if result.plan and result.plan.get("plan_id"):
            entry["plan_id"] = result.plan["plan_id"]
            entry["queue_warnings"] = _detect_queue_warnings(result.plan, queue_index)
        else:
            entry["queue_warnings"] = []
        results.append(entry)

        if result.ok:
            print(f"OK {rel_str}")
        else:
            failures += 1
            print(f"FAIL {rel_str}", file=sys.stderr)
            for err in result.errors:
                print(f"  - {err}", file=sys.stderr)

    exit_code = 0 if failures == 0 else 2

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = (ROOT / output_path).resolve()
    else:
        output_path = _default_summary_path()

    _write_summary(results, output=output_path, strict=args.strict, exit_code=exit_code)
    rel_out = _relative_to_root(output_path)
    print(f"wrote summary to {rel_out}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
