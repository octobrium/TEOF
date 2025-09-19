"""Shared helpers for receipts tooling."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator, Sequence

ROOT = Path(__file__).resolve().parents[2]
PLANS_DIR = ROOT / "_plans"

PlanPath = Path
ReceiptEntry = tuple[PlanPath, str]


def resolve_plan_paths(paths: Sequence[str] | None = None) -> list[PlanPath]:
    """Resolve plan paths relative to repo root."""

    if paths:
        resolved: list[PlanPath] = []
        for raw in paths:
            plan_path = Path(raw)
            if not plan_path.is_absolute():
                plan_path = ROOT / plan_path
            if not plan_path.exists():
                raise FileNotFoundError(f"plan not found: {raw}")
            resolved.append(plan_path)
        return resolved

    if not PLANS_DIR.exists():
        return []
    return sorted(PLANS_DIR.glob("*.plan.json"))


def iter_plan_receipts(plan_path: PlanPath) -> Iterator[ReceiptEntry]:
    """Yield `(plan_path, receipt)` tuples for plan-level and step receipts."""

    data = json.loads(plan_path.read_text(encoding="utf-8"))
    for entry in data.get("receipts", []) or []:
        yield (plan_path, entry)
    for step in data.get("steps", []) or []:
        for entry in step.get("receipts", []) or []:
            yield (plan_path, entry)


def find_missing_receipts(plan_paths: Iterable[PlanPath]) -> list[ReceiptEntry]:
    """Return list of `(plan_path, missing_receipt)` entries."""

    missing: list[ReceiptEntry] = []
    for plan in plan_paths:
        for _, receipt in iter_plan_receipts(plan):
            target = ROOT / receipt
            if not target.exists():
                missing.append((plan, receipt))
    return missing

__all__ = [
    "ROOT",
    "PLANS_DIR",
    "resolve_plan_paths",
    "iter_plan_receipts",
    "find_missing_receipts",
]
