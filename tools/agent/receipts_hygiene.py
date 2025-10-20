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
DEFAULT_WARN_THRESHOLD = 259200.0  # 3 days
DEFAULT_FAIL_THRESHOLD = 604800.0  # 7 days


def _relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _summary_latency_value(entry: Dict[str, Any]) -> Optional[float]:
    latencies = entry.get("latency_seconds", {}) or {}
    candidates: List[float] = []
    for key in ("plan_to_first_receipt", "note_to_first_receipt"):
        value = latencies.get(key)
        if isinstance(value, (int, float)) and value >= 0:
            candidates.append(float(value))
    if not candidates:
        return None
    return min(candidates)


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


def _build_alerts(
    plan_entries: List[Dict[str, Any]],
    warn_threshold: Optional[float],
    fail_threshold: Optional[float],
) -> Dict[str, Any]:
    alerts: List[Dict[str, Any]] = []
    warn_count = 0
    fail_count = 0

    for entry in plan_entries:
        plan_id = entry.get("plan_id")
        if not isinstance(plan_id, str) or not plan_id:
            continue
        fastest = _summary_latency_value(entry)
        if fastest is None:
            continue
        severity: Optional[str] = None
        if fail_threshold is not None and fastest >= fail_threshold:
            severity = "fail"
            fail_count += 1
        elif warn_threshold is not None and fastest >= warn_threshold:
            severity = "warn"
            warn_count += 1
        if severity is None:
            continue
        alerts.append(
            {
                "plan_id": plan_id,
                "severity": severity,
                "plan_to_first_seconds": entry.get("latency_seconds", {}).get("plan_to_first_receipt"),
                "note_to_first_seconds": entry.get("latency_seconds", {}).get("note_to_first_receipt"),
            }
        )

    return {
        "warn_threshold_seconds": warn_threshold,
        "fail_threshold_seconds": fail_threshold,
        "counts": {"warn": warn_count, "fail": fail_count},
        "alerts": alerts,
    }


def run_hygiene(
    *,
    root: Path,
    output_dir: Path,
    quiet: bool,
    fail_on_missing: bool = False,
    max_plan_latency: Optional[float] = None,
    warn_plan_latency: Optional[float] = None,
    fail_plan_latency: Optional[float] = None,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    receipts_dir = output_dir / "receipts-index"
    receipts_pointer = output_dir / "receipts-index-latest.jsonl"
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
        payload = receipts_index.build_index_payload(root, tracked=tracked)
        metrics_entries = receipts_metrics.build_metrics(root, output=metrics_path)
    finally:
        for key, value in original_index_attrs.items():
            setattr(receipts_index, key, value)
        for key, value in original_metrics_attrs.items():
            setattr(receipts_metrics, key, value)

    write_result = receipts_index.write_index(payload, receipts_dir, chunk_size=500)
    manifest_path = None
    for path in write_result.paths:
        if path.name == "manifest.json":
            manifest_path = path
            break

    if manifest_path is None:
        raise SystemExit("::error:: receipts index manifest missing")

    manifest_rel = _relative(manifest_path)
    pointer_entry = {
        "kind": "summary",
        **payload.summary,
    }
    manifest_entry = {
        "kind": "receipts_index_manifest",
        "manifest": manifest_rel,
        "chunk_size": 500,
    }
    with receipts_pointer.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(pointer_entry, ensure_ascii=False) + "\n")
        handle.write(json.dumps(manifest_entry, ensure_ascii=False) + "\n")

    plan_entries = [entry for entry in metrics_entries if entry.get("kind") == "plan_latency"]

    warn_threshold = warn_plan_latency if warn_plan_latency and warn_plan_latency > 0 else None
    fail_threshold = fail_plan_latency if fail_plan_latency and fail_plan_latency > 0 else None
    if warn_threshold and fail_threshold and warn_threshold > fail_threshold:
        raise SystemExit("warn threshold must be less than or equal to fail threshold")

    summary = {
        "generated_at": datetime.utcnow().replace(tzinfo=timezone.utc).strftime(ISO_FMT),
        "receipts_index_manifest": manifest_rel,
        "receipts_index_pointer": _relative(receipts_pointer),
        "receipts_latency": _relative(metrics_path),
        "metrics": _summarise_metrics(metrics_entries),
    }

    alerts = _build_alerts(plan_entries, warn_threshold, fail_threshold)
    if alerts["alerts"]:
        summary["slow_plan_alerts"] = alerts

    summary_path = output_dir / "receipts-hygiene-summary.json"
    _write_json(summary_path, summary)

    if not quiet:
        print("Receipts hygiene summary")
        print(f"  Receipts index manifest: {summary['receipts_index_manifest']}")
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
        if alerts["alerts"]:
            print("  Slow plan alerts:")
            for alert in alerts["alerts"]:
                print(
                    "    - {plan_id}: severity={severity}, plan_to_first={plan}, note_to_first={note}".format(
                        plan_id=alert["plan_id"],
                        severity=alert["severity"],
                        plan=alert["plan_to_first_seconds"],
                        note=alert["note_to_first_seconds"],
                    )
                )
        else:
            print("  Slow plan alerts: none")

    missing_count = summary["metrics"].get("plans_missing_receipts", 0) or 0
    slow_plans = summary["metrics"].get("slow_plans") or []
    if fail_on_missing and missing_count:
        raise SystemExit(f"missing receipts detected: {missing_count}")
    if max_plan_latency is not None:
        for plan_id, first_delta, note_delta in slow_plans:
            breach = first_delta and first_delta > max_plan_latency
            note_breach = note_delta and note_delta > max_plan_latency
            if breach or note_breach:
                raise SystemExit(
                    "plan latency threshold exceeded: "
                    f"{plan_id} first_receipt={first_delta} note_to_receipt={note_delta}"
                )

    if fail_threshold is not None and alerts["counts"]["fail"]:
        offenders = sorted(alert["plan_id"] for alert in alerts["alerts"] if alert["severity"] == "fail")
        raise SystemExit(
            "plan latency fail threshold exceeded: " + ", ".join(offenders)
        )

    return summary


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", help="Directory for hygiene outputs (default: _report/usage/)")
    parser.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    parser.add_argument("--quiet", action="store_true", help="Suppress console summary")
    parser.add_argument("--fail-on-missing", action="store_true", help="Exit non-zero if any plan is missing receipts")
    parser.add_argument(
        "--max-plan-latency",
        type=float,
        help="Exit non-zero if plan_to_first_receipt or note_to_first_receipt exceeds this many seconds",
    )
    parser.add_argument(
        "--warn-plan-latency",
        type=float,
        default=DEFAULT_WARN_THRESHOLD,
        help="Warn when plan latency exceeds this many seconds (0 to disable, default: 259200)",
    )
    parser.add_argument(
        "--fail-plan-latency",
        type=float,
        default=DEFAULT_FAIL_THRESHOLD,
        help="Fail when plan latency exceeds this many seconds (0 to disable, default: 604800)",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if args.output_dir:
        output_dir = Path(args.output_dir)
        if not output_dir.is_absolute():
            output_dir = (root / output_dir).resolve()
    else:
        output_dir = DEFAULT_USAGE_DIR

    try:
        run_hygiene(
            root=root,
            output_dir=output_dir,
            quiet=args.quiet,
            fail_on_missing=args.fail_on_missing,
            max_plan_latency=args.max_plan_latency,
            warn_plan_latency=args.warn_plan_latency,
            fail_plan_latency=args.fail_plan_latency,
        )
    except SystemExit as exc:
        raise
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
