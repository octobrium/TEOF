
#!/usr/bin/env python3
"""Check that plan-referenced receipts exist."""
from __future__ import annotations

import argparse
from pathlib import Path

from tools.receipts.utils import ROOT, find_missing_receipts, resolve_plan_paths


def checker(paths: list[str]) -> int:
    try:
        plan_paths = resolve_plan_paths(paths)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    missing = [
        (plan.relative_to(ROOT), receipt)
        for plan, receipt in find_missing_receipts(plan_paths)
    ]
    if missing:
        for plan, receipt in missing:
            print(f"Missing receipt: {plan} -> {receipt}")
        return 1
    print("All plan receipts found.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate presence of plan receipts")
    parser.add_argument("paths", nargs="*", help="Optional specific plan files to check")
    args = parser.parse_args(argv)
    return checker(args.paths)


if __name__ == "__main__":
    raise SystemExit(main())
