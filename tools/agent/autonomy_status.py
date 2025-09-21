#!/usr/bin/env python3
"""Summarise autonomy health: receipts hygiene + recent batch runs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
HYGIENE_SUMMARY = ROOT / "_report" / "usage" / "receipts-hygiene-summary.json"
BATCH_DIR = ROOT / "_report" / "usage" / "batch-refinement"


def _read_json(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def load_hygiene() -> Dict[str, Any] | None:
    return _read_json(HYGIENE_SUMMARY)


def load_batch_logs(limit: int | None = None) -> List[Dict[str, Any]]:
    if not BATCH_DIR.exists():
        return []
    files = sorted(BATCH_DIR.glob("batch-refinement-*.json"))
    if limit is not None:
        files = files[-limit:]
    entries: List[Dict[str, Any]] = []
    for path in files:
        data = _read_json(path)
        if data is None:
            continue
        data["_path"] = path
        entries.append(data)
    return entries


def summarise(hygiene: Dict[str, Any] | None, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    metrics = hygiene.get("metrics", {}) if isinstance(hygiene, dict) else {}
    missing = metrics.get("plans_missing_receipts")
    slow_plans = metrics.get("slow_plans") or []
    top_slow = [plan_id for plan_id, _, _ in slow_plans[:3]]

    latest_log = logs[-1] if logs else None
    failed_batches = [log for log in logs if log.get("operator_preset", {}).get("summary") == "fail"]
    warn_batches = [log for log in logs if log.get("operator_preset", {}).get("summary") == "warn"]

    return {
        "hygiene": {
            "generated_at": hygiene.get("generated_at") if hygiene else None,
            "plans_total": metrics.get("plans_total"),
            "plans_missing_receipts": missing,
            "missing_plan_ids": metrics.get("missing_plan_ids"),
            "slow_plans": slow_plans,
        },
        "batch_logs": {
            "entries": len(logs),
            "latest_summary": latest_log.get("operator_preset", {}).get("summary") if latest_log else None,
            "latest_agent": latest_log.get("agent") if latest_log else None,
            "latest_generated_at": latest_log.get("generated_at") if latest_log else None,
            "warn_count": len(warn_batches),
            "fail_count": len(failed_batches),
        },
        "top_slow_plans": top_slow,
    }


def print_human(summary: Dict[str, Any]) -> None:
    hygiene = summary["hygiene"]
    batch = summary["batch_logs"]
    print("Autonomy status")
    print(f"  Hygiene generated: {hygiene.get('generated_at')}")
    print(f"  Plans total: {hygiene.get('plans_total')} | missing: {hygiene.get('plans_missing_receipts')}")
    missing_ids = hygiene.get("missing_plan_ids") or []
    if missing_ids:
        print("  Missing plan ids:")
        for plan_id in missing_ids:
            print(f"    - {plan_id}")
    slow = hygiene.get("slow_plans") or []
    if slow:
        print("  Slow plans (top 3):")
        for plan_id, first_delta, note_delta in slow[:3]:
            print(f"    - {plan_id}: first_receipt={first_delta} note_to_receipt={note_delta}")
    else:
        print("  Slow plans: none")

    print(f"  Batch logs: total={batch['entries']} warn={batch['warn_count']} fail={batch['fail_count']}")
    print(
        "  Latest batch: summary="
        f"{batch['latest_summary']} agent={batch['latest_agent']} at={batch['latest_generated_at']}"
    )


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, help="Limit batch logs considered (default: all)")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    parser.add_argument(
        "--write",
        dest="write_path",
        help="Write summary JSON to path (default: _report/usage/autonomy-status.json)",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Skip writing the summary JSON receipt",
    )
    args = parser.parse_args(argv)

    hygiene = load_hygiene()
    logs = load_batch_logs(limit=args.limit)
    summary = summarise(hygiene, logs)

    default_write = not args.no_write
    target_path = None
    if args.write_path is not None:
        target_path = Path(args.write_path)
    elif default_write:
        target_path = Path("_report/usage/autonomy-status.json")

    if target_path is not None or args.json:
        payload = dict(summary)
        if logs:
            entries_detail = []
            for entry in logs:
                detail = {
                    "generated_at": entry.get("generated_at"),
                    "summary": entry.get("operator_preset", {}).get("summary"),
                    "agent": entry.get("agent"),
                }
                path = entry.get("_path")
                if isinstance(path, Path):
                    try:
                        detail["log_path"] = str(path.relative_to(ROOT))
                    except ValueError:
                        detail["log_path"] = str(path)
                entries_detail.append(detail)
            payload.setdefault("batch_logs", {})["entries_detail"] = entries_detail

    if target_path is not None:
        target = target_path
        if not target.is_absolute():
            target = ROOT / target
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_human(summary)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
