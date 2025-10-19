#!/usr/bin/env python3
"""Summarise autonomy health: receipts hygiene + recent batch runs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from tools.autonomy import macro_hygiene
from tools.autonomy.shared import write_receipt_payload
from tools.agent import receipt_brief

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


def summarise(
    hygiene: Dict[str, Any] | None,
    logs: List[Dict[str, Any]],
    macro: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    metrics = hygiene.get("metrics", {}) if isinstance(hygiene, dict) else {}
    slow_plan_alerts = hygiene.get("slow_plan_alerts") if isinstance(hygiene, dict) else None
    missing = metrics.get("plans_missing_receipts")
    slow_plans = metrics.get("slow_plans") or []
    top_slow = [plan_id for plan_id, _, _ in slow_plans[:3]]

    latest_log = logs[-1] if logs else None
    failed_batches = [log for log in logs if log.get("operator_preset", {}).get("summary") == "fail"]
    warn_batches = [log for log in logs if log.get("operator_preset", {}).get("summary") == "warn"]
    average_pytest = None
    average_hygiene = None
    metric_counts = 0
    pytest_total = 0.0
    hygiene_total = 0.0
    for entry in logs:
        metrics_entry = entry.get("metrics") or {}
        pytest_seconds = metrics_entry.get("pytest_seconds")
        hygiene_seconds = metrics_entry.get("hygiene_seconds")
        if isinstance(pytest_seconds, (int, float)) and isinstance(hygiene_seconds, (int, float)):
            metric_counts += 1
            pytest_total += pytest_seconds
            hygiene_total += hygiene_seconds
    if metric_counts:
        average_pytest = pytest_total / metric_counts
        average_hygiene = hygiene_total / metric_counts

    readiness_attention = []
    if missing:
        readiness_attention.append(
            {
                "kind": "missing_receipts",
                "count": missing,
                "plan_ids": metrics.get("missing_plan_ids") or [],
            }
        )
    slow_plan_attention = False
    alert_counts = (slow_plan_alerts or {}).get("counts") or {}
    if alert_counts.get("fail"):
        readiness_attention.append({"kind": "slow_plan_fail", "count": alert_counts["fail"]})
        slow_plan_attention = True
    elif alert_counts.get("warn"):
        readiness_attention.append({"kind": "slow_plan_warn", "count": alert_counts["warn"]})
        slow_plan_attention = True
    if slow_plan_attention:
        readiness_attention.append(
            {
                "kind": "slow_plans",
                "count": len(slow_plans),
                "plan_ids": [entry[0] for entry in slow_plans],
            }
        )
    if latest_log:
        latest_summary = latest_log.get("operator_preset", {}).get("summary")
        if latest_summary == "fail":
            readiness_attention.append({"kind": "batch_failures", "count": len(failed_batches)})
        elif latest_summary == "warn":
            readiness_attention.append({"kind": "batch_warnings", "count": len(warn_batches)})

    readiness = {
        "status": "ready" if not readiness_attention else "attention",
        "missing_receipts": missing or 0,
        "slow_plan_count": len(slow_plans),
        "slow_plan_alert_counts": alert_counts,
        "batch_warn_count": len(warn_batches),
        "batch_fail_count": len(failed_batches),
        "attention": readiness_attention,
    }

    plan_briefs: Dict[str, str] = {}
    candidate_plans: set[str] = set()
    for plan_id in metrics.get("missing_plan_ids") or []:
        if isinstance(plan_id, str):
            candidate_plans.add(plan_id)
    for entry in slow_plans:
        if isinstance(entry, (list, tuple)) and entry:
            plan_id = entry[0]
            if isinstance(plan_id, str):
                candidate_plans.add(plan_id)
    for plan_id in sorted(candidate_plans):
        try:
            brief_text = receipt_brief.generate_plan_brief(plan_id)
        except (FileNotFoundError, KeyError, ValueError):
            continue
        lines = brief_text.splitlines()
        if lines:
            plan_briefs[plan_id] = lines[0]

    summary = {
        "hygiene": {
            "generated_at": hygiene.get("generated_at") if hygiene else None,
            "plans_total": metrics.get("plans_total"),
            "plans_missing_receipts": missing,
            "missing_plan_ids": metrics.get("missing_plan_ids"),
            "slow_plans": slow_plans,
            "slow_plan_alerts": slow_plan_alerts,
        },
        "batch_logs": {
            "entries": len(logs),
            "latest_summary": latest_log.get("operator_preset", {}).get("summary") if latest_log else None,
            "latest_agent": latest_log.get("agent") if latest_log else None,
            "latest_generated_at": latest_log.get("generated_at") if latest_log else None,
            "warn_count": len(warn_batches),
            "fail_count": len(failed_batches),
            "avg_pytest_seconds": average_pytest,
            "avg_hygiene_seconds": average_hygiene,
        },
        "top_slow_plans": top_slow,
        "readiness": readiness,
    }
    if macro is not None:
        summary["macro_hygiene"] = macro
    if plan_briefs:
        summary["plan_briefs"] = plan_briefs
    return summary


def load_macro_hygiene(*, write_receipt: bool) -> Optional[Mapping[str, Any]]:
    try:
        status = macro_hygiene.compute_status()
    except Exception:
        return None
    if write_receipt:
        try:
            write_receipt_payload(macro_hygiene.DEFAULT_RECEIPT, status)
        except Exception:
            pass
    return status


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
    alerts = hygiene.get("slow_plan_alerts") or {}
    alert_counts = alerts.get("counts") or {}
    if alert_counts:
        print(f"  Slow plan alerts: warn={alert_counts.get('warn', 0)} fail={alert_counts.get('fail', 0)}")

    readiness = summary.get("readiness") or {}
    if readiness:
        status = readiness.get("status")
        if status:
            print(
                "  Readiness: "
                f"{status}"
                f" (missing={readiness.get('missing_receipts')} slow={readiness.get('slow_plan_count')}"
                f" warn={readiness.get('slow_plan_alert_counts', {}).get('warn', 0)}"
                f" fail={readiness.get('slow_plan_alert_counts', {}).get('fail', 0)}"
                f" batch_warn={readiness.get('batch_warn_count')} batch_fail={readiness.get('batch_fail_count')})"
            )
        attention_items = readiness.get("attention") or []
        if attention_items:
            print("  Readiness attention:")
            for item in attention_items:
                kind = item.get("kind")
                count = item.get("count")
                if kind == "missing_receipts":
                    plans = ", ".join(item.get("plan_ids", [])) or "none listed"
                    print(f"    - Missing receipts ({count}): {plans}")
                elif kind == "slow_plans":
                    plans = ", ".join(item.get("plan_ids", [])) or "unknown"
                    print(f"    - Slow plans ({count}): {plans}")
                elif kind == "slow_plan_fail":
                    print(f"    - Slow plan fail alerts ({count})")
                elif kind == "slow_plan_warn":
                    print(f"    - Slow plan warn alerts ({count})")
                elif kind == "batch_failures":
                    print(f"    - Batch failures in last runs ({count})")
                elif kind == "batch_warnings":
                    print(f"    - Batch warnings in last runs ({count})")

    plan_briefs = summary.get("plan_briefs") or {}
    if plan_briefs:
        print("Plan briefs:")
        for plan_id, brief in plan_briefs.items():
            print(f"  - {plan_id}: {brief}")

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
    macro = load_macro_hygiene(write_receipt=not args.no_write)
    summary = summarise(hygiene, logs, macro=macro)

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
