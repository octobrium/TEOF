#!/usr/bin/env python3
"""Normalize planner status fields and surface schema drift."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

ALLOWED_PLAN_STATUS = {"queued", "in_progress", "blocked", "done"}
ALLOWED_CHECKPOINT_STATUS = {"pending", "satisfied", "superseded"}
PLAN_STATUS_SYNONYMS = {
    "in-progress": "in_progress",
    "completed": "done",
    "complete": "done",
    "pending": "queued",
    "pending_review": "queued",
    "active": "in_progress",
    "closed": "done",
}
CHECKPOINT_STATUS_SYNONYMS = {
    "in-progress": "pending",
    "in_progress": "pending",
    "completed": "satisfied",
    "complete": "satisfied",
    "done": "satisfied",
}
ROOT = Path(__file__).resolve().parents[2]
PLAN_DIR = ROOT / "_plans"


@dataclass
class Finding:
    path: Path
    pointer: str
    value: str
    suggested: str | None
    severity: str  # "fixable" or "error"


@dataclass
class Fix:
    path: Path
    pointer: str
    original: str
    updated: str


def _iter_plan_paths(root: Path, explicit: Sequence[Path] | None) -> list[Path]:
    if explicit:
        paths: list[Path] = []
        for item in explicit:
            candidate = (root / item).resolve()
            if not candidate.exists():
                raise SystemExit(f"Plan not found: {candidate}")
            paths.append(candidate)
        return paths
    plans_dir = root / "_plans"
    if not plans_dir.exists():
        raise SystemExit(f"Plans directory missing: {plans_dir}")
    return sorted(plans_dir.glob("*.plan.json"))


def _normalize_status(value: str, allowed: set[str], synonyms: dict[str, str]) -> tuple[str, str | None]:
    cleaned = value.strip()
    lowered = cleaned.lower()
    if lowered in allowed:
        return lowered, None if cleaned == lowered else lowered
    if lowered in synonyms:
        return synonyms[lowered], synonyms[lowered]
    return cleaned, None


def _check_duplicates(
    items: Iterable[str],
    record: Callable[[str, str, str | None, str], None],
    pointer_prefix: str,
) -> None:
    seen: dict[str, int] = {}
    for index, item in enumerate(items):
        pointer = f"{pointer_prefix}[{index}]"
        if not isinstance(item, str):
            record(pointer, repr(item), None, "error")
            continue
        key = item.strip()
        previous = seen.get(key)
        if previous is not None:
            record(pointer, item, f"duplicate of index {previous}", "error")
        else:
            seen[key] = index


def _scan_plan(path: Path, apply: bool) -> tuple[list[Finding], list[Fix]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    findings: list[Finding] = []
    fixes: list[Fix] = []
    changed = False

    def record(pointer: str, value: str, suggested: str | None, severity: str) -> None:
        findings.append(Finding(path=path, pointer=pointer, value=value, suggested=suggested, severity=severity))

    def maybe_update(container: dict, key: str, pointer: str, allowed: set[str], synonyms: dict[str, str]) -> None:
        nonlocal changed
        raw = container.get(key)
        if raw is None:
            return
        if not isinstance(raw, str):
            record(pointer, repr(raw), None, "error")
            return
        normalized, suggested = _normalize_status(raw, allowed, synonyms)
        if normalized in allowed and normalized != raw:
            if apply:
                container[key] = normalized
                fixes.append(Fix(path=path, pointer=pointer, original=raw, updated=normalized))
                changed = True
            else:
                record(pointer, raw, normalized, "fixable")
            return
        if normalized not in allowed:
            record(pointer, raw, suggested, "error")
            return
        if raw != normalized:
            if apply:
                container[key] = normalized
                fixes.append(Fix(path=path, pointer=pointer, original=raw, updated=normalized))
                changed = True
            else:
                record(pointer, raw, normalized, "fixable")

    if isinstance(data, dict):
        maybe_update(data, "status", "status", ALLOWED_PLAN_STATUS, PLAN_STATUS_SYNONYMS)
        steps = data.get("steps")
        if isinstance(steps, list):
            for index, step in enumerate(steps):
                if isinstance(step, dict):
                    maybe_update(step, "status", f"steps[{index}].status", ALLOWED_PLAN_STATUS, PLAN_STATUS_SYNONYMS)
                    receipts = step.get("receipts")
                    if isinstance(receipts, list):
                        _check_duplicates(receipts, record, f"steps[{index}].receipts")
                    elif receipts is not None:
                        record(f"steps[{index}].receipts", repr(receipts), None, "error")
        checkpoint = data.get("checkpoint")
        if isinstance(checkpoint, dict):
            maybe_update(
                checkpoint,
                "status",
                "checkpoint.status",
                ALLOWED_CHECKPOINT_STATUS,
                CHECKPOINT_STATUS_SYNONYMS,
            )
        receipts = data.get("receipts")
        if isinstance(receipts, list):
            _check_duplicates(receipts, record, "receipts")
        elif receipts is not None:
            record("receipts", repr(receipts), None, "error")
    else:
        record("<root>", repr(data), None, "error")

    if apply and changed:
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return findings, fixes


def run(paths: Sequence[Path] | None, *, apply: bool, root: Path) -> int:
    plan_paths = _iter_plan_paths(root, paths)
    all_findings: list[Finding] = []
    all_fixes: list[Fix] = []

    for plan_path in plan_paths:
        findings, fixes = _scan_plan(plan_path, apply=apply)
        all_findings.extend(findings)
        all_fixes.extend(fixes)

    for fix in all_fixes:
        print(f"FIXED {fix.path.relative_to(root)} :: {fix.pointer}: '{fix.original}' -> '{fix.updated}'")

    errors = [f for f in all_findings if f.severity == "error"]
    fixables = [f for f in all_findings if f.severity == "fixable"]

    for finding in all_findings:
        rel = finding.path.relative_to(root)
        suggested = f" (suggested: {finding.suggested})" if finding.suggested else ""
        print(f"{finding.severity.upper()} {rel} :: {finding.pointer}: '{finding.value}'{suggested}")

    if errors:
        return 2
    if fixables and not apply:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Specific plan files to lint")
    parser.add_argument("--apply", action="store_true", help="Rewrite files in place to normalize statuses")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args.paths, apply=args.apply, root=args.root)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
