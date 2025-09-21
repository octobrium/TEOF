#!/usr/bin/env python3
"""Run receipts index + latency metrics and emit hygiene summary."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.agent import receipts_index, receipts_metrics

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_USAGE_DIR = ROOT / "_report" / "usage"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _summarise_metrics(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    plan_entries = [entry for entry in entries if entry.get("kind") == "plan_latency"]
    missing_plans = [entry for entry in plan_entries if entry.get("missing_receipts")]
    slow_plans = sorted(
        (
            (
                entry["plan_id"],
                entry["latency_seconds"].get("plan_to_first_receipt"),
                entry["latency_seconds"].get("note_to_first_receipt"),
            )
            for entry in plan_entries
        ),
        key=lambda item: (item[1] or 0, item[2] or 0),
        reverse=True,
    )[:5]
    return {
        "plans_total": len(plan_entries),
        "plans_missing_receipts": len(missing_plans),
        "missing_plan_ids": [entry["plan_id"] for entry in missing_plans][:10],
        "slow_plans": slow_plans,
    }


def run_hygiene(*, root: Path, output_dir: Path, quiet: bool) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    receipts_path = output_dir / "receipts-index-latest.jsonl"
    metrics_path = output_dir / "receipts-latency-latest.jsonl"

    original_index_attrs = {
        "ROOT": receipts_index.ROOT,
        "PLANS_DIR": receipts_index.PLANS_DIR,
        "REPORT_DIR": receipts_index.REPORT_DIR,
        "MANAGER_REPORT": receipts_index.MANAGER_REPORT,
        "DEFAULT_USAGE_DIR": receipts_index.DEFAULT_USAGE_DIR,
    }
    original_metrics_attrs = {
        "ROOT": receipts_metrics.ROOT,
        "DEFAULT_USAGE_DIR": receipts_metrics.DEFAULT_USAGE_DIR,
    }

    try:
        receipts_index.ROOT = root
        receipts_index.PLANS_DIR = root / "_plans"
        receipts_index.REPORT_DIR = root / "_report"
        receipts_index.MANAGER_REPORT = root / "_bus" / "messages" / "manager-report.jsonl"
        receipts_index.DEFAULT_USAGE_DIR = output_dir

        receipts_metrics.ROOT = root
        receipts_metrics.DEFAULT_USAGE_DIR = output_dir

        tracked = receipts_index._git_tracked_paths(root)
        index_entries = receipts_index.build_index(root, tracked=tracked)
        metrics_entries = receipts_metrics.build_metrics(root, output=metrics_path)
    finally:
        for key, value in original_index_attrs.items():
            setattr(receipts_index, key, value)
        for key, value in original_metrics_attrs.items():
            setattr(receipts_metrics, key, value)
    with receipts_path.open("w", encoding="utf-8") as handle:
        for entry in index_entries:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    summary = {
        "generated_at": datetime.utcnow().replace(tzinfo=timezone.utc).strftime(ISO_FMT),
        "receipts_index": _relative(receipts_path),
        "receipts_latency": _relative(metrics_path),
        "metrics": _summarise_metrics(metrics_entries),
    }

    summary_path = output_dir / "receipts-hygiene-summary.json"
    _write_json(summary_path, summary)

    if not quiet:
        print("Receipts hygiene summary")
        print(f"  Receipts index: {summary['receipts_index']}")
        print(f"  Receipts latency: {summary['receipts_latency']}")
        print(f"  Plans total: {summary['metrics']['plans_total']}")
        print(f"  Plans missing receipts: {summary['metrics']['plans_missing_receipts']}")
        slow = summary["metrics"]["slow_plans"]
        if slow:
            print("  Slow plans (plan_id, plan_to_first_receipt, note_to_first_receipt):")
            for plan_id, first_delta, note_delta in slow:
                print(f"    - {plan_id}: first_receipt={first_delta}, note_to_receipt={note_delta}")
        else:
            print("  Slow plans: none")

    return summary


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", help="Directory for hygiene outputs (default: _report/usage/)")
    parser.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    parser.add_argument("--quiet", action="store_true", help="Suppress console summary")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if args.output_dir:
        output_dir = Path(args.output_dir)
        if not output_dir.is_absolute():
            output_dir = (root / output_dir).resolve()
    else:
        output_dir = DEFAULT_USAGE_DIR

    run_hygiene(root=root, output_dir=output_dir, quiet=args.quiet)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
