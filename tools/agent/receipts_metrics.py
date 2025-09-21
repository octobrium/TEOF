#!/usr/bin/env python3
"""Compute latency metrics for plans, receipts, and manager reflections."""
from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from tools.agent import receipts_index

ROOT = Path(__file__).resolve().parents[2]
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
DEFAULT_USAGE_DIR = ROOT / "_report" / "usage"


def _parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.strptime(value, ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _summary(values: Iterable[Optional[float]]) -> Dict[str, Any]:
    numbers = [v for v in values if isinstance(v, (int, float))]
    if not numbers:
        return {"count": 0}
    return {
        "count": len(numbers),
        "min": min(numbers),
        "median": statistics.median(numbers),
        "max": max(numbers),
    }


def _build_receipt_map(entries: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    for entry in entries:
        if entry.get("kind") == "receipt":
            path = entry.get("path")
            if isinstance(path, str):
                mapping[path] = entry
    return mapping


def _build_manager_map(entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    mapping: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        if entry.get("kind") != "manager_message":
            continue
        plan_id = entry.get("plan_id")
        if isinstance(plan_id, str) and plan_id:
            mapping[plan_id].append(entry)
    return mapping


def _collect_plan_receipts(plan: Dict[str, Any], receipt_map: Dict[str, Dict[str, Any]]) -> tuple[List[float], List[str], Optional[str], Optional[str]]:
    created = _parse_datetime(plan.get("created"))
    receipt_times: List[datetime] = []
    missing: set[str] = set(plan.get("missing_receipts", []))

    def handle_receipt(info: Dict[str, Any]) -> None:
        rel = info.get("path")
        if not isinstance(rel, str):
            return
        rel = rel.strip()
        if not rel:
            return
        if not info.get("exists") or not info.get("tracked"):
            missing.add(rel)
            return
        meta = receipt_map.get(rel)
        if not meta:
            return
        mtime = _parse_datetime(meta.get("mtime"))
        if mtime:
            receipt_times.append(mtime)

    for rec in plan.get("receipts", []) or []:
        if isinstance(rec, dict):
            handle_receipt(rec)

    for step in plan.get("steps", []) or []:
        for rec in step.get("receipts", []) or []:
            if isinstance(rec, dict):
                handle_receipt(rec)

    receipt_times.sort()
    latencies: List[float] = []
    if created:
        for ts in receipt_times:
            latencies.append((ts - created).total_seconds())

    first_receipt_ts: Optional[datetime] = receipt_times[0] if receipt_times else None
    last_receipt_ts: Optional[datetime] = receipt_times[-1] if receipt_times else None

    return latencies, sorted(missing), (
        first_receipt_ts.strftime(ISO_FMT) if first_receipt_ts else None
    ), (
        last_receipt_ts.strftime(ISO_FMT) if last_receipt_ts else None
    )


def _collect_manager_notes(plan_id: str, manager_map: Dict[str, List[Dict[str, Any]]]) -> tuple[List[datetime], Optional[datetime]]:
    notes: List[datetime] = []
    for entry in manager_map.get(plan_id, []):
        timestamp = _parse_datetime(entry.get("timestamp"))
        if not timestamp:
            continue
        notes.append(timestamp)
    notes.sort()
    first_note = notes[0] if notes else None
    return notes, first_note


def _compute_plan_metrics(plan: Dict[str, Any], receipt_map: Dict[str, Dict[str, Any]], manager_map: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    plan_id = plan.get("plan_id")
    created = _parse_datetime(plan.get("created"))

    latencies, missing_receipts, first_receipt_ts, last_receipt_ts = _collect_plan_receipts(plan, receipt_map)
    first_delta = latencies[0] if latencies else None
    last_delta = latencies[-1] if latencies else None
    notes, first_note = _collect_manager_notes(plan_id, manager_map)

    note_to_plan = (first_note - created).total_seconds() if first_note and created else None
    note_to_receipt = None
    if first_note and first_receipt_ts:
        receipt_dt = _parse_datetime(first_receipt_ts)
        if receipt_dt:
            note_to_receipt = (receipt_dt - first_note).total_seconds()

    plan_metrics = {
        "kind": "plan_latency",
        "plan_id": plan_id,
        "status": plan.get("status"),
        "created": plan.get("created"),
        "checkpoint_status": plan.get("checkpoint_status"),
        "receipt_count": len(latencies),
        "missing_receipts": missing_receipts,
        "latency_seconds": {
            "plan_to_first_receipt": first_delta,
            "plan_to_last_receipt": last_delta,
            "note_to_plan": note_to_plan,
            "note_to_first_receipt": note_to_receipt,
        },
        "first_receipt_ts": first_receipt_ts,
        "last_receipt_ts": last_receipt_ts,
        "manager_notes": len(notes),
        "manager_first_ts": first_note.strftime(ISO_FMT) if first_note else None,
    }
    return plan_metrics


def build_metrics(root: Path, *, output: Optional[Path]) -> List[Dict[str, Any]]:
    tracked = receipts_index._git_tracked_paths(root)  # reuse cached helper if available
    entries = receipts_index.build_index(root, tracked=tracked)
    receipt_map = _build_receipt_map(entries)
    manager_map = _build_manager_map(entries)
    plan_entries = [entry for entry in entries if entry.get("kind") == "plan"]

    plan_metrics = [_compute_plan_metrics(plan, receipt_map, manager_map) for plan in plan_entries]

    first_receipt_latencies = [metrics["latency_seconds"]["plan_to_first_receipt"] for metrics in plan_metrics]
    manager_receipt_latencies = [metrics["latency_seconds"]["note_to_first_receipt"] for metrics in plan_metrics]
    missing_count = sum(1 for metrics in plan_metrics if metrics["missing_receipts"])

    summary = {
        "kind": "summary",
        "generated_at": datetime.utcnow().replace(tzinfo=timezone.utc).strftime(ISO_FMT),
        "counts": {
            "plans": len(plan_metrics),
            "plans_with_missing_receipts": missing_count,
        },
        "latency_seconds": {
            "plan_to_first_receipt": _summary(first_receipt_latencies),
            "note_to_first_receipt": _summary(manager_receipt_latencies),
        },
    }

    output_entries = [summary, *plan_metrics]

    if output is None:
        for entry in output_entries:
            print(json.dumps(entry, ensure_ascii=False))
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            for entry in output_entries:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"wrote metrics to {_relative(output)}")

    return output_entries


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="Write JSONL output to this path (relative paths land under _report/usage/)")
    parser.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = (DEFAULT_USAGE_DIR / output_path).resolve()
    else:
        output_path = None

    build_metrics(root, output=output_path)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
