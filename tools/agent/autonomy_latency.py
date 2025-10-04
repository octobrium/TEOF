#!/usr/bin/env python3
"""Sentinel that raises bus alerts when autonomy receipts show slow plans."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping, Optional

from tools.agent import autonomy_status, bus_event, receipts_hygiene

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RECEIPT = ROOT / "_report" / "usage" / "autonomy-latency.json"


def _pick_fastest(first: Optional[float], note: Optional[float]) -> Optional[float]:
    candidates = [val for val in (first, note) if isinstance(val, (int, float))]
    if not candidates:
        return None
    return min(candidates)


def _emit_alert(
    plan_id: str,
    payload: Mapping[str, object],
    *,
    dry_run: bool,
    severity: str,
) -> None:
    summary = f"Autonomy latency: {plan_id} slow receipts ({severity})"
    if dry_run:
        print(json.dumps({"summary": summary, "payload": payload}, ensure_ascii=False, indent=2))
        return
    args = argparse.Namespace(
        agent="autonomy-sentinel",
        event="alert",
        summary=summary,
        task=None,
        plan=plan_id,
        branch=None,
        pr=None,
        receipt=None,
        extra=[
            f"first_receipt={payload.get('first_receipt_seconds')}",
            f"note_receipt={payload.get('note_to_receipt_seconds')}",
            "topic=autonomy-latency",
            f"severity={severity}",
        ],
        severity="high" if severity == "fail" else "warn",
        consensus_decision=None,
        consensus_output=None,
        consensus_meta=None,
    )
    bus_event.handle_log(args)


def check_latency(
    *,
    threshold: Optional[float] = None,
    warn_threshold: Optional[float] = None,
    fail_threshold: Optional[float] = None,
    dry_run: bool = False,
    limit: int | None = None,
    write: bool = True,
    output: Optional[Path] = None,
) -> Dict[str, object]:
    """Check autonomy status for slow plans and emit alerts with severity."""

    hygiene = autonomy_status.load_hygiene()
    logs = autonomy_status.load_batch_logs(limit=limit)
    summary = autonomy_status.summarise(hygiene, logs)
    hygiene_info = summary.get("hygiene", {})
    slow_plans = hygiene_info.get("slow_plans") or []
    hygiene_alerts = (hygiene_info.get("slow_plan_alerts") or {}).get("alerts") or []

    if warn_threshold is None:
        warn_threshold = hygiene_info.get("slow_plan_alerts", {}).get("warn_threshold_seconds")
        if warn_threshold is None:
            warn_threshold = receipts_hygiene.DEFAULT_WARN_THRESHOLD
    if fail_threshold is None:
        fail_threshold = hygiene_info.get("slow_plan_alerts", {}).get("fail_threshold_seconds")
        if fail_threshold is None:
            fail_threshold = receipts_hygiene.DEFAULT_FAIL_THRESHOLD
    if threshold is not None:
        fail_threshold = threshold
        if warn_threshold is None or warn_threshold > fail_threshold:
            warn_threshold = fail_threshold

    warn_threshold = warn_threshold if warn_threshold and warn_threshold > 0 else None
    fail_threshold = fail_threshold if fail_threshold and fail_threshold > 0 else None

    if warn_threshold and fail_threshold and warn_threshold > fail_threshold:
        raise SystemExit("warn threshold must be <= fail threshold")

    candidate_records: List[Dict[str, object]] = []
    if hygiene_alerts:
        for alert in hygiene_alerts:
            if not isinstance(alert, dict):
                continue
            candidate_records.append(
                {
                    "plan_id": alert.get("plan_id"),
                    "plan_to_first": alert.get("plan_to_first_seconds"),
                    "note_to_first": alert.get("note_to_first_seconds"),
                }
            )
    else:
        for record in slow_plans:
            if not isinstance(record, (list, tuple)) or len(record) < 1:
                continue
            candidate_records.append(
                {
                    "plan_id": record[0],
                    "plan_to_first": record[1] if len(record) > 1 else None,
                    "note_to_first": record[2] if len(record) > 2 else None,
                }
            )

    alerts: List[Dict[str, object]] = []
    for record in candidate_records:
        plan_id = record.get("plan_id")
        if not isinstance(plan_id, str) or not plan_id:
            continue
        first_delta = record.get("plan_to_first")
        note_delta = record.get("note_to_first")
        fastest = _pick_fastest(first_delta, note_delta)
        if fastest is None:
            continue
        severity: Optional[str] = None
        if fail_threshold is not None and fastest >= fail_threshold:
            severity = "fail"
        elif warn_threshold is not None and fastest >= warn_threshold:
            severity = "warn"
        if severity is None:
            continue
        payload = {
            "plan_id": plan_id,
            "first_receipt_seconds": first_delta,
            "note_to_receipt_seconds": note_delta,
            "warn_threshold_seconds": warn_threshold,
            "fail_threshold_seconds": fail_threshold,
            "severity": severity,
        }
        alerts.append(payload)
        _emit_alert(plan_id, payload, dry_run=dry_run, severity=severity)

    receipt_path = None
    if write:
        target = output or DEFAULT_RECEIPT
        if not target.is_absolute():
            target = ROOT / target
        target.parent.mkdir(parents=True, exist_ok=True)
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        counts = {"warn": 0, "fail": 0}
        for alert in alerts:
            if alert.get("severity") == "fail":
                counts["fail"] += 1
            elif alert.get("severity") == "warn":
                counts["warn"] += 1
        receipt = {
            "generated_at": generated_at,
            "warn_threshold_seconds": warn_threshold,
            "fail_threshold_seconds": fail_threshold,
            "alerts": alerts,
            "slow_count": len(alerts),
            "counts": counts,
        }
        target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        receipt_path = target
    return {"alerts": alerts, "receipt_path": receipt_path}


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--threshold",
        type=float,
        help="Legacy single threshold (seconds) – sets fail threshold and warn if unset",
    )
    parser.add_argument(
        "--warn-threshold",
        type=float,
        default=receipts_hygiene.DEFAULT_WARN_THRESHOLD,
        help="Warn when latency exceeds this many seconds (0 to disable, default: 259200)",
    )
    parser.add_argument(
        "--fail-threshold",
        type=float,
        default=receipts_hygiene.DEFAULT_FAIL_THRESHOLD,
        help="Fail when latency exceeds this many seconds (0 to disable, default: 604800)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print alerts instead of logging to the bus")
    parser.add_argument("--limit", type=int, help="Limit batch logs considered when summarising")
    parser.add_argument(
        "--output",
        help="Write receipt JSON to path (default: _report/usage/autonomy-latency.json)",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Skip writing the latency receipt",
    )
    args = parser.parse_args(argv)

    output_path = Path(args.output) if args.output else None
    check_latency(
        threshold=args.threshold,
        warn_threshold=args.warn_threshold,
        fail_threshold=args.fail_threshold,
        dry_run=args.dry_run,
        limit=args.limit,
        write=not args.no_write,
        output=output_path,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
