#!/usr/bin/env python3
"""Sentinel that raises bus alerts when autonomy receipts show slow plans."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional

from tools.agent import autonomy_status, bus_event

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RECEIPT = ROOT / "_report" / "usage" / "autonomy-latency.json"


def _format_slow_plans(records: Iterable[tuple[str, float | None, float | None]]) -> List[Dict[str, object]]:
    formatted: List[Dict[str, object]] = []
    for plan_id, first_delta, note_delta in records:
        formatted.append(
            {
                "plan_id": plan_id,
                "first_receipt_seconds": first_delta,
                "note_to_receipt_seconds": note_delta,
            }
        )
    return formatted


def _emit_alert(plan_id: str, payload: Mapping[str, object], *, dry_run: bool) -> None:
    summary = f"Autonomy latency: {plan_id} slow receipts"
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
        extra=[f"first_receipt={payload.get('first_receipt_seconds')}", f"note_receipt={payload.get('note_to_receipt_seconds')}", "topic=autonomy-latency"],
        severity="warn",
        consensus_decision=None,
        consensus_output=None,
        consensus_meta=None,
    )
    bus_event.handle_log(args)


def check_latency(
    *,
    threshold: float,
    dry_run: bool = False,
    limit: int | None = None,
    write: bool = True,
    output: Optional[Path] = None,
) -> Dict[str, object]:
    """Check autonomy status for slow plans and emit alerts.

    Returns the list of alert payloads for inspection/testing.
    """

    hygiene = autonomy_status.load_hygiene()
    logs = autonomy_status.load_batch_logs(limit=limit)
    summary = autonomy_status.summarise(hygiene, logs)
    slow_plans = summary.get("hygiene", {}).get("slow_plans") or []
    alerts: List[Dict[str, object]] = []
    for record in slow_plans:
        if not isinstance(record, (list, tuple)) or len(record) < 1:
            continue
        plan_id = str(record[0])
        first_delta = record[1] if len(record) > 1 else None
        note_delta = record[2] if len(record) > 2 else None
        fastest = min([d for d in (first_delta, note_delta) if isinstance(d, (int, float))], default=None)
        if fastest is None or fastest <= threshold:
            continue
        payload = {
            "plan_id": plan_id,
            "first_receipt_seconds": first_delta,
            "note_to_receipt_seconds": note_delta,
            "threshold_seconds": threshold,
        }
        alerts.append(payload)
        _emit_alert(plan_id, payload, dry_run=dry_run)
    receipt_path = None
    if write:
        target = output or DEFAULT_RECEIPT
        if not target.is_absolute():
            target = ROOT / target
        target.parent.mkdir(parents=True, exist_ok=True)
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        receipt = {
            "generated_at": generated_at,
            "threshold_seconds": threshold,
            "alerts": alerts,
            "slow_count": len(alerts),
        }
        target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        receipt_path = target
    return {"alerts": alerts, "receipt_path": receipt_path}


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--threshold",
        type=float,
        default=86400.0,
        help="Maximum allowed latency in seconds before alerting (default: 86400s)",
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
        dry_run=args.dry_run,
        limit=args.limit,
        write=not args.no_write,
        output=output_path,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
