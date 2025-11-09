#!/usr/bin/env python3
"""Utilities for authoring planner artifacts."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, List

from tools.planner import queue_warnings
from tools.planner.systemic_targets import (
    derive_layer_targets,
    ensure_axes,
    highest_axis_value,
    parse_axis_tokens,
)
from tools.planner.validate import PLAN_STATUS, STEP_STATUS, strict_checks, validate_plan
from tools.receipts.scaffold import scaffold_plan, format_created, ScaffoldError

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLAN_DIR = ROOT / "_plans"
EXPLORATORY_DEFAULT_EXPIRY_HOURS = 72
CLAIMS_DIR = ROOT / "_bus" / "claims"
SLUG_NORMALIZER = re.compile(r"[^a-z0-9-]+")
PLAN_ID_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
PLAN_STATUS_VALUES = tuple(sorted(PLAN_STATUS))
STEP_STATUS_VALUES = tuple(sorted(STEP_STATUS))
LEGACY_STATUS = {"pending": "queued"}
CMD_PLACEHOLDER = "(CMD-__)"
LAYER_CHOICES = tuple(f"L{i}" for i in range(7))
SYSTEMIC_SCALE_CHOICES = tuple(range(1, 11))


class PlannerCliError(RuntimeError):
    """Raised when a planner CLI command cannot complete."""


def _parse_layer_tokens(text: str) -> list[str]:
    tokens = re.split(r"[,\s/|]+", text)
    layers: list[str] = []
    for token in tokens:
        cleaned = token.strip().upper()
        if cleaned.startswith("L") and len(cleaned) >= 2 and cleaned[1].isdigit():
            value = cleaned[:2]
            if value not in layers:
                layers.append(value)
    return layers


def _load_queue_entry(ref: str) -> tuple[list[str], list[str], list[str]]:
    path = ROOT / ref
    if not path.exists():
        raise PlannerCliError(f"queue reference not found: {ref}")
    coordinates: list[str] = []
    systemic_targets: list[str] = []
    layer_targets: list[str] = []
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PlannerCliError(f"unable to read queue entry {ref}: {exc}") from exc
    for raw_line in content.splitlines():
        line = raw_line.strip()
        lowered = line.lower()
        if lowered.startswith("coordinate:"):
            value = line.split(":", 1)[1].strip()
            if value:
                coordinates.append(value)
        elif lowered.startswith("systemic targets:"):
            value = line.split(":", 1)[1].strip()
            systemic_targets = parse_axis_tokens(value)
        elif lowered.startswith("layer targets:"):
            value = line.split(":", 1)[1].strip()
            layer_targets = _parse_layer_tokens(value)
    return coordinates, systemic_targets, layer_targets


def _parse_coordinate_token(token: str) -> tuple[int | None, str | None]:
    token = token.strip()
    if not token or ":" not in token:
        return None, None
    left, right = token.split(":", 1)
    systemic: int | None = None
    layer: str | None = None
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


def _resolve_queue_metadata(
    queue_refs: list[str],
    layer: str | None,
    systemic_scale: int | None,
) -> tuple[str | None, int | None, list[dict[str, str]], list[str], list[str]]:
    if not queue_refs:
        return layer, systemic_scale, [], [], []
    links: list[dict[str, str]] = []
    systemic_tokens: list[str] = []
    layer_hints: list[str] = []
    queue_layer_targets: list[str] = []
    for raw_ref in queue_refs:
        ref = Path(raw_ref).as_posix()
        coordinates, systemic_from_queue, layer_targets_queue = _load_queue_entry(ref)

        links.append({"type": "queue", "ref": ref})

        coordinate_pairs = [_parse_coordinate_token(coord) for coord in coordinates]
        systemic_candidates = [value for value, _ in coordinate_pairs if value is not None]
        layer_candidates = [value for _, value in coordinate_pairs if value]

        if systemic_candidates:
            if systemic_scale is None:
                systemic_scale = systemic_candidates[0]
            elif systemic_scale not in systemic_candidates:
                raise PlannerCliError(
                    f"queue {ref} expects systemic_scale in {systemic_candidates} but got {systemic_scale}"
                )
            for candidate in systemic_candidates:
                if candidate is None:
                    continue
                token = f"S{candidate}"
                if token not in systemic_tokens:
                    systemic_tokens.append(token)
        if systemic_from_queue:
            for axis in systemic_from_queue:
                if axis not in systemic_tokens:
                    systemic_tokens.append(axis)

        if layer_candidates:
            if layer is None:
                layer = layer_candidates[0]
            elif layer not in layer_candidates:
                raise PlannerCliError(
                    f"queue {ref} expects layer in {layer_candidates} but got {layer}"
                )
            for candidate in layer_candidates:
                if candidate and candidate not in layer_hints:
                    layer_hints.append(candidate)
        if layer_targets_queue:
            for target in layer_targets_queue:
                if target not in queue_layer_targets:
                    queue_layer_targets.append(target)

    return layer, systemic_scale, links, systemic_tokens, layer_hints + queue_layer_targets


def _render_warning_table(warnings: list[dict[str, Any]]) -> str:
    if not warnings:
        return "No planner queue warnings detected."
    headers = ("plan", "queue", "issue", "message")
    widths = [len(header) for header in headers]
    rows: list[tuple[str, str, str, str]] = []
    for warning in warnings:
        plan_id = str(warning.get("plan_id", "-"))
        queue_ref = str(warning.get("queue_ref", "-"))
        issue = str(warning.get("issue", "-"))
        message = str(warning.get("message", "-"))
        row = (plan_id, queue_ref, issue, message)
        rows.append(row)
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))
    header_line = " | ".join(header.ljust(widths[idx]) for idx, header in enumerate(headers))
    divider = " | ".join("-" * widths[idx] for idx in range(len(headers)))
    lines = [header_line, divider]
    for row in rows:
        lines.append(" | ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row)))
    return "\n".join(lines)


def _default_actor() -> str:
    """Return the git user.name when available, else 'unknown'."""
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return "unknown"
    name = result.stdout.strip()
    return name or "unknown"


def _normalize_slug(slug: str) -> str:
    slug = slug.strip().lower()
    slug = SLUG_NORMALIZER.sub("-", slug)
    slug = slug.strip("-")
    return slug


def _normalize_impact_ref(value: str | None, fallback: str) -> str:
    if value is None:
        return fallback
    slug = _normalize_slug(value)
    if not slug:
        raise PlannerCliError("--impact-ref must contain alphanumeric characters")
    return slug


def _parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return datetime.utcnow()
    try:
        return datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise PlannerCliError("timestamp must be ISO8601 UTC (e.g., 2025-09-17T00:00:00Z)") from exc


def _normalize_status(value: str, *, allowed: Iterable[str]) -> str:
    if not isinstance(value, str):
        raise PlannerCliError("status must be a string")
    lowered = value.strip().lower()
    lowered = LEGACY_STATUS.get(lowered, lowered)
    if lowered not in allowed:
        raise PlannerCliError(f"status must be one of {sorted(set(allowed))}")
    return lowered


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _ensure_priority(value: int | None) -> int:
    if value is None:
        raise PlannerCliError("--priority is required")
    if value < 0:
        raise PlannerCliError("--priority must be >= 0")
    return value


def _ensure_systemic_scale(value: int | None) -> int:
    if value is None:
        raise PlannerCliError("--systemic-scale is required")
    if value not in SYSTEMIC_SCALE_CHOICES:
        raise PlannerCliError("--systemic-scale must be between 1 and 10")
    return value


def _ensure_impact_score(value: int | None) -> int:
    if value is None:
        raise PlannerCliError("--impact-score is required")
    if value < 0:
        raise PlannerCliError("--impact-score must be >= 0")
    return value


def _parse_steps(raw_steps: List[str], *, summary: str) -> List[dict]:
    if not raw_steps:
        return [
            {
                "id": "S1",
                "title": summary,
                "status": "queued",
                "notes": CMD_PLACEHOLDER,
                "receipts": [],
            }
        ]

    steps: List[dict] = []
    seen_ids: set[str] = set()
    for idx, entry in enumerate(raw_steps, 1):
        if ":" not in entry:
            raise PlannerCliError(f"step {idx} must use format 'ID:Title'")
        sid, title = entry.split(":", 1)
        sid = sid.strip()
        title = title.strip()
        if not sid or not title:
            raise PlannerCliError(f"step {idx} requires non-empty id and title")
        if sid in seen_ids:
            raise PlannerCliError(f"duplicate step id '{sid}'")
        seen_ids.add(sid)
        steps.append({"id": sid, "title": title, "status": "queued", "notes": CMD_PLACEHOLDER, "receipts": []})
    return steps


def _write_plan(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")


def _load_plan(path: Path) -> dict:
    if not path.exists():
        raise PlannerCliError(f"plan not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _ensure_valid(path: Path) -> None:
    result = validate_plan(path, strict=False)
    if not result.ok:
        raise PlannerCliError("plan validation failed: " + "; ".join(result.errors))
    strict_errors = strict_checks(result.plan, repo_root=ROOT) if result.plan else []
    if strict_errors:
        raise PlannerCliError("plan strict checks failed: " + "; ".join(strict_errors))


def _active_claims_for_plan(plan_id: str) -> list[Path]:
    matches: list[Path] = []
    if not CLAIMS_DIR.exists():
        return matches
    for claim_path in CLAIMS_DIR.glob("*.json"):
        try:
            payload = json.loads(claim_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if payload.get("plan_id") == plan_id and payload.get("status") in {"active", "paused"}:
            matches.append(claim_path)
    return matches


def _enforce_claim_guard(plan_id: str, allow_unclaimed: bool) -> None:
    if allow_unclaimed:
        return
    if _active_claims_for_plan(plan_id):
        return
    hint = (
        "Run 'python -m tools.agent.bus_claim claim --task <TASK_ID> --plan {plan_id}' "
        "before creating the plan, or pass --allow-unclaimed to bypass (manager override)."
    ).format(plan_id=plan_id)
    raise PlannerCliError(
        "bus_claim guard: no active claim references plan_id '"
        + plan_id
        + "'. "
        + hint
    )


def cmd_new(args: argparse.Namespace) -> int:
    slug = _normalize_slug(args.slug)
    if not slug:
        raise PlannerCliError("slug must contain at least one alphanumeric character")

    is_exploratory = bool(getattr(args, "exploratory", False))
    timestamp = _parse_timestamp(args.timestamp)
    plan_id = f"{timestamp:%Y-%m-%d}-{slug}"
    if not PLAN_ID_PATTERN.match(plan_id):
        raise PlannerCliError(
            "plan_id derived from slug is invalid; ensure slug uses lowercase letters, numbers, or hyphens"
        )

    if not is_exploratory:
        _enforce_claim_guard(plan_id, getattr(args, "allow_unclaimed", False))

    provided_plan_dir = Path(args.plan_dir).resolve()
    if (
        is_exploratory
        and provided_plan_dir == DEFAULT_PLAN_DIR.resolve()
    ):
        plan_dir = provided_plan_dir / "exploratory"
    else:
        plan_dir = provided_plan_dir
    plan_path = plan_dir / f"{plan_id}.plan.json"
    if plan_path.exists() and not args.force:
        raise PlannerCliError(f"plan already exists: {plan_path}")

    actor = args.actor or _default_actor()
    summary = args.summary.strip()
    if not summary:
        raise PlannerCliError("summary must be non-empty")

    owner = (args.owner or actor).strip() or actor
    checkpoint_desc = args.checkpoint or "Define verification + receipts"
    steps = _parse_steps(args.step, summary=summary)

    priority_arg = getattr(args, "priority", None)
    if is_exploratory and priority_arg is None:
        priority = 9
    else:
        priority = _ensure_priority(priority_arg)
    systemic_arg_tokens: list[str] = []
    for token in getattr(args, "systemic_target", []):
        systemic_arg_tokens.extend(parse_axis_tokens(token))
    provided_systemic_targets: list[str] = []
    if systemic_arg_tokens:
        try:
            provided_systemic_targets = ensure_axes(systemic_arg_tokens)
        except ValueError as exc:
            raise PlannerCliError(str(exc)) from exc
    layer_arg = getattr(args, "layer", None)
    layer = layer_arg.upper() if layer_arg else None
    if is_exploratory and layer is None:
        layer = "L5"
    scale_arg = getattr(args, "systemic_scale", None)
    systemic_scale = scale_arg
    scale_provided = scale_arg is not None
    impact_arg = getattr(args, "impact_score", None)
    if is_exploratory and impact_arg is None:
        impact_score = 10
    else:
        impact_score = _ensure_impact_score(impact_arg)
    impact_ref_arg = getattr(args, "impact_ref", None)
    impact_ref = _normalize_impact_ref(impact_ref_arg, plan_id)
    queue_refs: list[str] = [ref for ref in getattr(args, "queue_ref", []) if ref]
    (
        layer,
        systemic_scale,
        queue_links,
        queue_systemic_targets,
        queue_layer_hints,
    ) = _resolve_queue_metadata(
        queue_refs,
        layer,
        systemic_scale,
    )

    systemic_targets: list[str] = []
    if provided_systemic_targets:
        systemic_targets = provided_systemic_targets
    elif queue_systemic_targets:
        systemic_targets = queue_systemic_targets
    elif systemic_scale is not None:
        systemic_targets = [f"S{systemic_scale}"]
    elif is_exploratory:
        systemic_targets = ["S4"]
    if not systemic_targets:
        raise PlannerCliError(
            "unable to derive systemic targets; provide --systemic-target or reference a queue entry with them"
        )
    try:
        systemic_targets = ensure_axes(systemic_targets)
    except ValueError as exc:
        raise PlannerCliError(str(exc)) from exc

    if layer is None or layer not in LAYER_CHOICES:
        raise PlannerCliError(f"layer must be one of {', '.join(LAYER_CHOICES)} (provide manually or via --queue-ref)")
    layer_targets = derive_layer_targets(layer, queue_layer_hints)

    axis_highest = highest_axis_value(systemic_targets)
    if axis_highest is None:
        if systemic_scale is None:
            if is_exploratory:
                systemic_scale = 4
            else:
                raise PlannerCliError("--systemic-scale is required (unable to infer from systemic targets)")
    else:
        if systemic_scale is None:
            systemic_scale = axis_highest
        elif systemic_scale < axis_highest:
            if scale_provided:
                raise PlannerCliError(
                    f"--systemic-scale must be at least S{axis_highest} to cover systemic targets"
                )
            systemic_scale = axis_highest
    scale_token = f"S{systemic_scale}"
    if scale_token not in systemic_targets:
        systemic_targets.append(scale_token)
        systemic_targets = ensure_axes(systemic_targets)
    axis_highest = highest_axis_value(systemic_targets)
    if axis_highest and axis_highest > 4 and "S4" not in systemic_targets:
        systemic_targets.append("S4")
        systemic_targets = ensure_axes(systemic_targets)
    axis_highest = highest_axis_value(systemic_targets)
    if axis_highest is not None and systemic_scale != axis_highest:
        if scale_provided:
            raise PlannerCliError(
                f"--systemic-scale must equal highest systemic targets axis (expected S{axis_highest})"
            )
        systemic_scale = axis_highest
    systemic_scale = _ensure_systemic_scale(systemic_scale)

    payload = {
        "version": 0,
        "plan_id": plan_id,
        "created": f"{timestamp:%Y-%m-%dT%H:%M:%SZ}",
        "actor": actor,
        "summary": summary,
        "impact_ref": impact_ref,
        "systemic_targets": systemic_targets,
        "layer_targets": layer_targets,
        "priority": priority,
        "layer": layer,
        "systemic_scale": systemic_scale,
        "impact_score": impact_score,
        "status": "queued",
        "steps": steps,
        "checkpoint": {
            "description": checkpoint_desc,
            "owner": owner,
            "status": "pending",
        },
        "links": queue_links,
        "receipts": [],
    }

    if is_exploratory:
        expiry_hours_arg = getattr(args, "expiry_hours", None)
        expiry_hours = expiry_hours_arg if isinstance(expiry_hours_arg, int) and expiry_hours_arg > 0 else EXPLORATORY_DEFAULT_EXPIRY_HOURS
        expires_at = timestamp + timedelta(hours=expiry_hours)
        payload["lane"] = "exploratory"
        payload["exploratory"] = {
            "expires_at": f"{expires_at:%Y-%m-%dT%H:%M:%SZ}",
            "horizon_hours": expiry_hours,
        }

    _write_plan(plan_path, payload)
    try:
        _ensure_valid(plan_path)
    except Exception:
        plan_path.unlink(missing_ok=True)
        raise

    scaffold_message: str | None = None
    if getattr(args, "scaffold", False):
        try:
            result = scaffold_plan(plan_id, agent=actor, include_design=True)
        except ScaffoldError as exc:
            raise PlannerCliError(f"scaffold failed: {exc}") from exc
        scaffold_message = format_created(result.created)

    print(plan_path)
    if scaffold_message:
        print(scaffold_message)
    return 0


def _resolve_plan_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_dir():
        raise PlannerCliError("plan path must be a file, not directory")
    if path.exists():
        return path.resolve()

    slug = raw
    for suffix in (".plan.json", ".plan", ".json"):
        if slug.endswith(suffix):
            slug = slug[: -len(suffix)]
            break
    candidate = DEFAULT_PLAN_DIR / f"{slug}.plan.json"
    if candidate.exists():
        return candidate

    if not path.suffix:
        candidate = DEFAULT_PLAN_DIR / f"{raw}.plan.json"
        if candidate.exists():
            return candidate

    raise PlannerCliError(f"plan not found: {raw}")


STATUS_TRANSITIONS = {
    "queued": {"queued", "in_progress", "blocked", "done"},
    "in_progress": {"in_progress", "blocked", "done"},
    "blocked": {"blocked", "in_progress", "done"},
    "done": {"done"},
}


def _guard_transition(current: str, new: str, *, context: str) -> None:
    allowed = STATUS_TRANSITIONS.get(current, {current})
    if new not in allowed:
        raise PlannerCliError(
            f"illegal status transition for {context}: {current} → {new}"
        )




def _format_step_line(step: dict) -> str:
    receipts = step.get("receipts") or []
    notes = step.get("notes")
    lines = [f"- {step.get('id')} [{step.get('status')}] {step.get('title')}"]
    if notes:
        lines.append(f"    note: {notes}")
    if receipts:
        lines.append(f"    receipts: {', '.join(receipts)}")
    return '\n'.join(lines)


def cmd_show(args: argparse.Namespace) -> int:
    plan_path = _resolve_plan_path(args.plan)
    result = validate_plan(plan_path, strict=args.strict)
    if not result.ok or result.plan is None:
        for err in result.errors:
            print(f"error: {err}", file=sys.stderr)
        return 2

    plan = result.plan
    created = plan.get("created")
    created_iso = created.strftime("%Y-%m-%dT%H:%M:%SZ") if isinstance(created, datetime) else str(created)
    print(f"plan_id: {plan.get('plan_id')}")
    print(f"summary: {plan.get('summary')}")
    print(f"impact_ref: {plan.get('impact_ref')}")
    print(f"status: {plan.get('status')}")
    print(f"created: {created_iso}")
    checkpoint = plan.get('checkpoint') or {}
    print(
        "checkpoint: "
        f"{checkpoint.get('status')} — {checkpoint.get('description')} "
        f"(owner: {checkpoint.get('owner')})"
    )
    steps = plan.get("steps") or []
    if steps:
        print("steps:")
        for step in steps:
            print(_format_step_line(step))
    receipts = plan.get("receipts") or []
    if receipts:
        print("plan receipts: " + ", ".join(receipts))
    return 0


def _collect_plan_rows(strict: bool) -> tuple[List[dict], List[tuple[Path, List[str]]]]:
    rows: List[dict] = []
    failures: List[tuple[Path, List[str]]] = []
    warning_index: dict[str, List[dict[str, Any]]] = {}
    for warning in queue_warnings.load_queue_warnings(ROOT):
        plan_id = str(warning.get("plan_id") or warning.get("plan") or "")
        if not plan_id:
            continue
        warning_index.setdefault(plan_id, []).append(warning)
    for path in sorted(DEFAULT_PLAN_DIR.glob("*.plan.json")):
        result = validate_plan(path, strict=strict)
        if not result.ok or result.plan is None:
            failures.append((path, result.errors))
            continue
        plan = result.plan
        raw_plan = _load_plan(path)
        steps = plan.get("steps") or []
        total_steps = len(steps)
        done_steps = sum(1 for step in steps if step.get("status") == "done")
        priority_val = _safe_int((raw_plan or {}).get("priority"))
        impact_val = _safe_int((raw_plan or {}).get("impact_score"))
        layer_val = (raw_plan or {}).get("layer")
        scale_val = (raw_plan or {}).get("systemic_scale")
        plan_id = plan.get("plan_id")
        warnings_for_plan = warning_index.get(plan_id, []) if plan_id else []
        rows.append(
            {
                "plan_id": plan_id,
                "status": plan.get("status"),
                "checkpoint": (plan.get("checkpoint") or {}).get("status"),
                "steps_total": total_steps,
                "steps_done": done_steps,
                "receipts": len(plan.get("receipts") or []),
                "queue_warnings": len(warnings_for_plan),
                "priority": priority_val,
                "layer": layer_val,
                "systemic_scale": scale_val,
                "impact": impact_val,
                "path": str(path.relative_to(ROOT)),
            }
        )
    rows.sort(
        key=lambda row: (
            row["priority"] if row["priority"] is not None else 9999,
            -row["impact"] if row.get("impact") is not None else 0,
            row["plan_id"],
        )
    )
    return rows, failures


def _print_plan_table(rows: List[dict]) -> None:
    if not rows:
        print("(no plans found)")
        return

    headers = ["plan_id", "priority", "layer", "scale", "impact", "status", "checkpoint", "steps", "receipts", "warnings"]
    widths = {key: len(key) for key in headers}
    formatted: List[dict] = []
    for row in rows:
        cell_map = {
            "plan_id": row["plan_id"],
            "priority": row.get("priority", "-"),
            "layer": row.get("layer", "-"),
            "scale": row.get("systemic_scale", "-"),
            "impact": row.get("impact", "-"),
            "status": row["status"],
            "checkpoint": row["checkpoint"] or "-",
            "steps": f"{row['steps_done']}/{row['steps_total']}",
            "receipts": str(row["receipts"]),
            "warnings": str(row.get("queue_warnings", 0)),
        }
        for key, value in cell_map.items():
            widths[key] = max(widths[key], len(str(value)))
        formatted.append(cell_map)

    def format_row(cell_map: dict) -> str:
        return "  ".join(str(cell_map[key]).ljust(widths[key]) for key in headers)

    print(format_row({key: key for key in headers}))
    print("  ".join("-" * widths[key] for key in headers))
    for cell_map in formatted:
        print(format_row(cell_map))

    counter = Counter(row["status"] for row in rows)
    summary = ", ".join(f"{status}={counter[status]}" for status in sorted(counter))
    print(f"\nplans: {len(rows)} ({summary})")


def cmd_list(args: argparse.Namespace) -> int:
    rows, failures = _collect_plan_rows(strict=args.strict)
    if failures:
        for path, errs in failures:
            print(f"error:{path.relative_to(ROOT)}", file=sys.stderr)
            for err in errs:
                print(f"  - {err}", file=sys.stderr)
        return 2

    if args.format == "json":
        payload = [
            {
                "plan_id": row["plan_id"],
                "priority": row.get("priority"),
                "layer": row.get("layer"),
                "systemic_scale": row.get("systemic_scale"),
                "impact_score": row.get("impact"),
                "status": row["status"],
                "checkpoint": row["checkpoint"],
                "steps": {"done": row["steps_done"], "total": row["steps_total"]},
                "receipts": row["receipts"],
                "queue_warnings": row.get("queue_warnings", 0),
                "path": row["path"],
            }
            for row in rows
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_plan_table(rows)
    return 0

def cmd_status(args: argparse.Namespace) -> int:
    plan_path = _resolve_plan_path(args.plan)
    data = _load_plan(plan_path)
    new_status = _normalize_status(args.status, allowed=PLAN_STATUS_VALUES)
    current = data.get("status", "queued")
    _guard_transition(current, new_status, context="plan")
    data["status"] = new_status
    _write_plan(plan_path, data)
    _ensure_valid(plan_path)
    print(f"status={new_status}")
    return 0


def cmd_step_add(args: argparse.Namespace) -> int:
    plan_path = _resolve_plan_path(args.plan)
    data = _load_plan(plan_path)
    steps = data.setdefault("steps", [])
    existing_ids = {step.get("id") for step in steps if isinstance(step, dict)}
    if args.id:
        step_id = args.id.strip()
        if not step_id:
            raise PlannerCliError("--id must be non-empty when provided")
        if step_id in existing_ids:
            raise PlannerCliError(f"step id '{step_id}' already exists")
    else:
        idx = 1
        step_id = f"S{idx}"
        while step_id in existing_ids:
            idx += 1
            step_id = f"S{idx}"

    description = args.desc.strip()
    if not description:
        raise PlannerCliError("--desc must be non-empty")

    steps.append(
        {
            "id": step_id,
            "title": description,
            "status": "queued",
            "notes": args.note if args.note is not None else CMD_PLACEHOLDER,
            "receipts": [],
        }
    )
    _write_plan(plan_path, data)
    _ensure_valid(plan_path)
    print(step_id)
    return 0


def cmd_step_set(args: argparse.Namespace) -> int:
    plan_path = _resolve_plan_path(args.plan)
    data = _load_plan(plan_path)
    steps = data.get("steps", [])
    for step in steps:
        if step.get("id") == args.step_id:
            current = _normalize_status(step.get("status", "queued"), allowed=STEP_STATUS_VALUES)
            new_status = _normalize_status(args.status, allowed=STEP_STATUS_VALUES)
            _guard_transition(current, new_status, context=f"step {args.step_id}")
            step["status"] = new_status
            if args.note is not None:
                step["notes"] = args.note
            break
    else:
        raise PlannerCliError(f"no step with id '{args.step_id}'")

    _write_plan(plan_path, data)
    _ensure_valid(plan_path)
    print(f"{args.step_id}={new_status}")
    return 0


def _relative_receipt(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError as exc:
        raise PlannerCliError("receipt must live inside repository") from exc


def cmd_attach_receipt(args: argparse.Namespace) -> int:
    plan_path = _resolve_plan_path(args.plan)
    data = _load_plan(plan_path)
    rel_receipt = _relative_receipt(Path(args.file))

    target_step = None
    for step in data.get("steps", []):
        if step.get("id") == args.step_id:
            target_step = step
            break
    if not target_step:
        raise PlannerCliError(f"no step with id '{args.step_id}'")

    receipts = list(target_step.get("receipts", []))
    if rel_receipt not in receipts:
        receipts.append(rel_receipt)
    target_step["receipts"] = receipts

    plan_receipts = set(data.get("receipts", []))
    plan_receipts.add(rel_receipt)
    data["receipts"] = sorted(plan_receipts)

    receipt_path = ROOT / rel_receipt
    if not receipt_path.exists():
        raise PlannerCliError(f"receipt not found: {rel_receipt}")
    try:
        payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PlannerCliError(f"receipt must be valid JSON: {rel_receipt}") from exc

    if isinstance(payload, dict):
        changed = False
        if payload.get("plan_id") != data.get("plan_id"):
            payload["plan_id"] = data.get("plan_id")
            changed = True
        if payload.get("plan_step_id") != args.step_id:
            payload["plan_step_id"] = args.step_id
            changed = True
        if changed:
            receipt_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _write_plan(plan_path, data)
    _ensure_valid(plan_path)
    print(rel_receipt)
    return 0


def cmd_warnings(args: argparse.Namespace) -> int:
    warnings = queue_warnings.load_queue_warnings(ROOT)
    if args.format == "json":
        payload = {
            "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "warnings": warnings,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_render_warning_table(warnings))
    if args.fail_on_warning and warnings:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="planner", description="Planner authoring helpers")
    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new", help="Create a plan skeleton")
    new.add_argument("slug", help="slug portion of plan_id (lowercase preferred)")
    new.add_argument("--summary", required=True, help="One-line intent for the plan")
    new.add_argument("--actor", help="Actor to record; defaults to git user.name")
    new.add_argument("--owner", help="Checkpoint owner; defaults to actor")
    new.add_argument("--checkpoint", help="Checkpoint description")
    new.add_argument(
        "--step",
        action="append",
        default=[],
        help="Add a step in format ID:Title (may be repeated)",
    )
    new.add_argument("--priority", type=int, help="Numeric priority (0 = highest)")
    new.add_argument(
        "--systemic-target",
        action="append",
        default=[],
        help="Systemic axis tokens (e.g. S1,S2). May be repeated; comma-separated values supported.",
    )
    new.add_argument("--layer", choices=LAYER_CHOICES, help="Layer label (L0–L6)")
    new.add_argument(
        "--systemic-scale",
        type=int,
        choices=SYSTEMIC_SCALE_CHOICES,
        help="Systemic axis (S1–S10)",
    )
    new.add_argument("--impact-score", type=int, help="Relative impact score (>=0)")
    new.add_argument("--impact-ref", help="Impact ledger slug (defaults to plan_id)")
    new.add_argument(
        "--queue-ref",
        action="append",
        default=[],
        help="Attach queue/<id>.md references and auto-populate metadata",
    )
    new.add_argument("--plan-dir", default=str(DEFAULT_PLAN_DIR), help="Directory for plan artifacts")
    new.add_argument("--timestamp", help="Override creation timestamp (UTC, e.g. 2025-09-17T00:00:00Z)")
    new.add_argument("--force", action="store_true", help="Overwrite existing plan if present")
    new.add_argument(
        "--allow-unclaimed",
        action="store_true",
        help="Bypass bus_claim guard (manager override)",
    )
    scaffold_group = new.add_mutually_exclusive_group()
    scaffold_group.add_argument(
        "--scaffold",
        dest="scaffold",
        action="store_true",
        help="Create a default receipt scaffold for the plan",
    )
    scaffold_group.add_argument(
        "--no-scaffold",
        dest="scaffold",
        action="store_false",
        help="Skip scaffold generation (default)",
    )
    new.add_argument(
        "--exploratory",
        action="store_true",
        help="Create the plan inside the exploratory sandbox lane with relaxed metadata defaults",
    )
    new.add_argument(
        "--expiry-hours",
        type=int,
        help="Override exploratory auto-expiry horizon in hours (default 72)",
    )
    new.set_defaults(func=cmd_new, scaffold=False, allow_unclaimed=False)

    status = sub.add_parser("status", help="Update the overall plan status")
    status.add_argument("plan", help="Path or plan_id of the plan JSON")
    status.add_argument("status", choices=PLAN_STATUS_VALUES, help="New status")
    status.set_defaults(func=cmd_status)

    plist = sub.add_parser("list", help="List plans and their statuses")
    plist.add_argument("--format", choices=["table", "json"], default="table")
    plist.add_argument("--strict", action="store_true", help="Validate plans strictly before listing")
    plist.set_defaults(func=cmd_list)

    show = sub.add_parser("show", help="Display plan summary")
    show.add_argument("plan", help="Plan path or id")
    show.add_argument("--strict", action="store_true", help="Validate with strict checks before printing")
    show.set_defaults(func=cmd_show)
    step_add = sub.add_parser("step", help="Modify steps")
    step_sub = step_add.add_subparsers(dest="step_cmd", required=True)

    step_add_parser = step_sub.add_parser("add", help="Add a new step")
    step_add_parser.add_argument("plan", help="Plan path or id")
    step_add_parser.add_argument("--desc", required=True, help="Step description/title")
    step_add_parser.add_argument("--id", help="Optional step id (default next S#)")
    step_add_parser.add_argument("--note", help="Optional notes for the step")
    step_add_parser.set_defaults(func=cmd_step_add)

    step_set_parser = step_sub.add_parser("set", help="Update an existing step")
    step_set_parser.add_argument("plan", help="Plan path or id")
    step_set_parser.add_argument("step_id", help="Step identifier")
    step_set_parser.add_argument("--status", required=True, choices=STEP_STATUS_VALUES)
    step_set_parser.add_argument("--note", help="Replace the step notes")
    step_set_parser.set_defaults(func=cmd_step_set)

    attach = sub.add_parser("attach-receipt", help="Attach a receipt to a step")
    attach.add_argument("plan", help="Plan path or id")
    attach.add_argument("step_id", help="Step identifier to receive the receipt")
    attach.add_argument("--file", required=True, help="Path to receipt JSON")
    attach.set_defaults(func=cmd_attach_receipt)

    warn = sub.add_parser("warnings", help="Show queue metadata warnings from the latest validation run")
    warn.add_argument("--format", choices=["table", "json"], default="table")
    warn.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Exit with status 1 when warnings are present",
    )
    warn.set_defaults(func=cmd_warnings)

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
        return args.func(args)
    except PlannerCliError as exc:
        parser.error(str(exc))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
