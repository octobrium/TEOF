"""Generate retro advisories from fractal conformance gaps."""
from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from tools.fractal import conformance

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFORMANCE_RECEIPT = REPO_ROOT / "_report" / "fractal" / "conformance" / "latest.json"
DEFAULT_OUT = REPO_ROOT / "_report" / "fractal" / "advisories" / "latest.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_coordinates(raw: Iterable[str]) -> tuple[Optional[int], Optional[str]]:
    for coord in raw:
        coord = coord.strip()
        if not coord:
            continue
        if ":" not in coord:
            continue
        left, right = coord.split(":", 1)
        try:
            systemic = int(left.strip().lstrip("S"))
        except ValueError:
            systemic = None
        layer = right.strip().upper()
        if layer and not layer.startswith("L"):
            layer = None
        return systemic, layer
    return None, None


def _base_advisory(path: str, source_receipt: str, claim: str, systemic: Optional[int], layer: Optional[str]) -> dict:
    advisory_id = f"ADV-{uuid.uuid4().hex[:8]}"
    ocers_trait = "Self-repair"
    direction = "up"
    payload = {
        "id": advisory_id,
        "created": _now_iso(),
        "source_receipt": source_receipt,
        "layer": layer or "L5",
        "systemic_scale": systemic,
        "ocers_target": {
            "trait": ocers_trait,
            "direction": direction,
        },
        "targets": [path],
        "claim": claim,
        "evidence": {
            "receipts": [source_receipt],
            "notes": "Generated from fractal conformance gap"
        },
        "expected_gain": {
            "ocers_delta": {ocers_trait: 0.01}
        },
        "severity": "medium",
    }
    return payload


def _queue_advisories(entries: List[conformance.QueueEntry], source_receipt: str) -> List[dict]:
    advisories: List[dict] = []
    for entry in entries:
        if not entry.issues:
            continue
        systemic, layer = _load_coordinates(entry.coordinates)
        claim = f"Queue item {entry.path} is missing: {', '.join(entry.issues)}"
        advisories.append(_base_advisory(entry.path, source_receipt, claim, systemic, layer))
    return advisories


def _plan_advisories(entries: List[conformance.PlanEntry], source_receipt: str) -> List[dict]:
    advisories: List[dict] = []
    for entry in entries:
        if not entry.issues:
            continue
        systemic = entry.systemic_scale
        layer = entry.layer
        claim = f"Plan {entry.plan_id} ({entry.path}) is missing: {', '.join(entry.issues)}"
        advisories.append(_base_advisory(entry.path, source_receipt, claim, systemic, layer))
    return advisories


def _memory_advisories(entries: List[conformance.MemoryEntry], source_receipt: str) -> List[dict]:
    advisories: List[dict] = []
    for entry in entries:
        if not entry.issues:
            continue
        claim = f"Memory entry #{entry.index} ({entry.summary}) is missing: {', '.join(entry.issues)}"
        advisories.append(_base_advisory(f"memory/log.jsonl#{entry.index}", source_receipt, claim, entry.systemic_scale, entry.layer))
    return advisories


def build_advisories(source_receipt: Path) -> List[dict]:
    queue_index = conformance.gather_queue_entries()
    queue_entries = list(queue_index.values())
    plan_entries = conformance.gather_plan_entries(queue_index)
    memory_entries = conformance.gather_memory_entries()

    advisories: List[dict] = []
    advisories.extend(_queue_advisories(queue_entries, str(source_receipt)))
    advisories.extend(_plan_advisories(plan_entries, str(source_receipt)))
    advisories.extend(_memory_advisories(memory_entries, str(source_receipt)))
    return advisories


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_CONFORMANCE_RECEIPT, help="Path to the conformance receipt informing these advisories")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Where to write advisories JSON")
    parser.add_argument("--empty-ok", action="store_true", help="Return success even if advisories list is empty")
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    source_receipt = args.source
    if not source_receipt.exists():
        source_receipt.parent.mkdir(parents=True, exist_ok=True)
        source_receipt.write_text(json.dumps(conformance.build_report(strict=False), indent=2) + "\n", encoding="utf-8")

    advisories = build_advisories(source_receipt)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": _now_iso(),
        "source_receipt": str(source_receipt),
        "advisories": advisories,
    }
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(advisories)} advisories → {args.out.relative_to(REPO_ROOT)}")

    if advisories or args.empty_ok:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
