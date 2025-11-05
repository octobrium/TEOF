"""Helpers for locating and normalising receipt references."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence

from teof._paths import repo_root
from tools.autonomy.shared import load_json

ROOT = repo_root(default=Path(__file__).resolve().parents[2])
DEFAULT_PLANS_DIR = ROOT / "_plans"


def normalise_receipts(values: Iterable[str] | None) -> List[str]:
    if not values:
        return []
    seen: set[str] = set()
    results: List[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        if value not in seen:
            seen.add(value)
            results.append(value)
    return results


def load_plan(plan_id: str, *, plans_dir: Path | None = None) -> Mapping[str, object]:
    base_dir = plans_dir or DEFAULT_PLANS_DIR
    path = base_dir / f"{plan_id}.plan.json"
    if not path.exists():
        raise FileNotFoundError(f"plan not found: {plan_id}")
    data = load_json(path)
    if not isinstance(data, Mapping):
        raise ValueError(f"plan malformed: {plan_id}")
    return data


def collect_plan_receipts(plan_id: str, *, plans_dir: Path | None = None) -> List[str]:
    plan = load_plan(plan_id, plans_dir=plans_dir)
    receipts = normalise_receipts(plan.get("receipts"))
    for step in plan.get("steps", []) or []:
        if not isinstance(step, Mapping):
            continue
        step_receipts = normalise_receipts(step.get("receipts"))
        for entry in step_receipts:
            if entry not in receipts:
                receipts.append(entry)
    return receipts


def compute_receipt_digest(receipts: Sequence[str]) -> str:
    joined = "\n".join(receipts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def resolve_item_receipts(
    item: Mapping[str, object],
    *,
    plans_dir: Path | None = None,
) -> List[str]:
    receipts = item.get("receipts")
    if isinstance(receipts, list):
        return normalise_receipts(receipts)
    ref = item.get("receipts_ref")
    if isinstance(ref, Mapping):
        if ref.get("kind") == "plan":
            plan_id = ref.get("plan_id")
            if isinstance(plan_id, str):
                return collect_plan_receipts(plan_id, plans_dir=plans_dir)
    return []
