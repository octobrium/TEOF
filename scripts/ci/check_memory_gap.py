#!/usr/bin/env python3
"""CI guard to ensure recent plans are represented in memory/log.jsonl."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence

from tools.memory import gap_audit


def _iso_window(hours: float) -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return cutoff.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _format_missing(entries: Sequence[dict]) -> str:
    lines = []
    for entry in entries:
        plan_id = entry.get("plan_id")
        plan_path = entry.get("plan_path")
        receipts = entry.get("missing_receipts") or []
        lines.append(f"- {plan_id} ({plan_path}) missing {len(receipts)} receipts")
        for receipt in receipts[:5]:
            lines.append(f"    • {receipt}")
        if len(receipts) > 5:
            lines.append(f"    • … {len(receipts) - 5} more")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--since",
        help="ISO timestamp to audit from (default: now - window-hours)",
    )
    parser.add_argument(
        "--window-hours",
        type=float,
        default=72.0,
        help="Fallback time window when --since is not provided (default: 72h)",
    )
    parser.add_argument("--plan", dest="plans", action="append", help="Plan id filter (repeatable)")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("_report/analysis/memory-gap/ci-latest.json"),
        help="Output receipt path (default: _report/analysis/memory-gap/ci-latest.json)",
    )
    parser.add_argument(
        "--max-missing",
        type=int,
        default=0,
        help="Allow this many missing plans before failing (default: 0)",
    )
    args = parser.parse_args(argv)

    since_value = args.since or _iso_window(args.window_hours)
    summary, out_path = gap_audit.run_audit(since_value, args.window_hours, args.plans, args.out)

    missing = summary.get("missing") or []
    print(f"[memory-gap] audited {summary['total']} plans → missing={len(missing)} receipt sets")
    print(f"[memory-gap] receipt → {out_path}")
    if len(missing) > args.max_missing:
        details = _format_missing(missing)
        if details:
            print(details)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
