
#!/usr/bin/env python3
"""Wrapper for receipts tooling."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.receipts.check import checker as run_check


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Receipts utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="Ensure receipts referenced by plans exist")
    check.add_argument("paths", nargs="*", help="Optional plan paths to check")

    args = parser.parse_args(argv)
    if args.command == "check":
        return run_check(args.paths)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
