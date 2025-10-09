#!/usr/bin/env python3
"""Fail guardrails when CLI commands lack tests or receipts."""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

from tools.maintenance import capability_inventory as inventory


def main() -> int:
    stale_days_env = os.environ.get("CAPABILITY_STALE_DAYS", "30")
    try:
        stale_days = float(stale_days_env)
    except ValueError:
        print(f"::error::Invalid CAPABILITY_STALE_DAYS value: {stale_days_env}")
        return 2

    entries = inventory.generate_inventory(stale_days=stale_days)
    now = datetime.now(timezone.utc)
    threshold = timedelta(days=stale_days)

    missing_tests = [entry for entry in entries if not entry.tests]
    stale_entries = [
        entry
        for entry in entries
        if entry.last_receipt is None or now - entry.last_receipt > threshold
    ]

    has_error = False
    if missing_tests:
        has_error = True
        names = ", ".join(sorted(entry.name for entry in missing_tests))
        print(f"::error::Commands missing regression coverage: {names}")
    if stale_entries:
        has_error = True
        names = ", ".join(
            f"{entry.name}(last={entry.last_receipt.isoformat() if entry.last_receipt else 'never'})"
            for entry in sorted(stale_entries, key=lambda e: e.name)
        )
        print(
            "::error::Commands lacking receipts within "
            f"{stale_days} days: {names}"
        )

    if has_error:
        return 1

    print(
        f"capability inventory: {len(entries)} commands OK "
        f"(stale threshold {stale_days}d)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
