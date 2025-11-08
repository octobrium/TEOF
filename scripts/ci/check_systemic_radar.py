#!/usr/bin/env python3
"""CI guard ensuring systemic radar receipts stay fresh."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from tools.autonomy.shared import load_json

ROOT = Path(__file__).resolve().parents[2]
RADAR_DIR = ROOT / "_report" / "usage" / "systemic-radar"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check systemic radar freshness")
    parser.add_argument("--max-age-hours", type=int, default=24, help="Maximum acceptable receipt age (default: 24h)")
    return parser.parse_args()


def latest_receipt() -> Path | None:
    files = sorted(RADAR_DIR.glob("systemic-radar-*.json"), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def main() -> int:
    args = parse_args()
    receipt = latest_receipt()
    if not receipt:
        print("No systemic radar receipt found under _report/usage/systemic-radar/", file=sys.stderr)
        return 1
    data = load_json(receipt)
    if not isinstance(data, dict) or "generated_at" not in data:
        print(f"Receipt missing generated_at: {receipt}", file=sys.stderr)
        return 1
    generated = data["generated_at"]
    try:
        timestamp = datetime.fromisoformat(generated.replace("Z", "+00:00"))
    except ValueError:
        print(f"Invalid generated_at timestamp: {generated}", file=sys.stderr)
        return 1
    age = datetime.now(timezone.utc) - timestamp
    if age > timedelta(hours=args.max_age_hours):
        print(f"Systemic radar receipt stale ({age} > {args.max_age_hours}h): {receipt}", file=sys.stderr)
        return 1
    summary = data.get("summary", {})
    print(f"Systemic radar ok: {receipt.name} summary={summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
