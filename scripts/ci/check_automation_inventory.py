#!/usr/bin/env python3
"""Warn when automation modules lack receipts or tests."""
from __future__ import annotations

import os
import sys
from datetime import timedelta

from tools.maintenance import automation_inventory as inventory


def main() -> int:
    stale_days_env = os.environ.get("AUTOMATION_STALE_DAYS", "30")
    try:
        stale_days = float(stale_days_env)
    except ValueError:
        print(f"::error::Invalid AUTOMATION_STALE_DAYS value: {stale_days_env}")
        return 2

    entries = inventory.generate_inventory(stale_days=stale_days)
    threshold = timedelta(days=stale_days)

    missing_receipts = [entry for entry in entries if not entry.receipts]
    stale_receipts = [entry for entry in entries if entry.last_receipt and entry.is_stale(threshold)]
    missing_tests = [entry for entry in entries if not entry.tests]

    has_error = False
    if stale_receipts:
        has_error = True
        details = ", ".join(
            f"{entry.module}(last={entry.last_receipt.isoformat() if entry.last_receipt else 'never'})"
            for entry in stale_receipts
        )
        print(
            "::error::Automation receipts stale or missing within "
            f"{stale_days} days: {details}"
        )

    missing_no_receipt = [entry for entry in missing_receipts if entry.last_receipt is None]
    if missing_no_receipt:
        names = ", ".join(entry.module for entry in missing_no_receipt)
        print(f"::warning::Automation modules missing receipts: {names}")

    if missing_tests:
        names = ", ".join(entry.module for entry in missing_tests)
        print(f"::notice::No direct tests detected for automation modules: {names}")

    if not has_error:
        print(
            f"automation inventory: {len(entries)} modules checked (stale threshold {stale_days}d)"
        )
    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main())
