
#!/usr/bin/env python3
"""Check that plan-referenced receipts exist."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLANS_DIR = ROOT / "_plans"


def iter_receipts(plan_path: Path):
    data = json.loads(plan_path.read_text(encoding="utf-8"))
    for entry in data.get("receipts", []) or []:
        yield plan_path, entry
    for step in data.get("steps", []) or []:
        for entry in step.get("receipts", []) or []:
            yield plan_path, entry


def checker(paths: list[str]) -> int:
    missing = []
    files = [Path(p) for p in paths] if paths else sorted(PLANS_DIR.glob("*.plan.json"))
    for plan in files:
        for _, receipt in iter_receipts(plan):
            path = ROOT / receipt
            if not path.exists():
                missing.append((plan.relative_to(ROOT), receipt))
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
