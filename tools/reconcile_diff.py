#!/usr/bin/env python3
"""Compare two reconciliation hello packets."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.reconcile_utils import compare_packets, load_packet


def main() -> int:
    parser = argparse.ArgumentParser(description="Diff reconciliation hello packets")
    parser.add_argument("left", help="Path to left hello packet (JSON)")
    parser.add_argument("right", help="Path to right hello packet (JSON)")
    args = parser.parse_args()

    left = load_packet(Path(args.left))
    right = load_packet(Path(args.right))

    diffs = compare_packets(left, right)
    if diffs:
        print("differences detected:")
        for line in diffs:
            print(" -", line)
        return 1
    else:
        print("hello packets match (commandments, anchors, receipts, capabilities)")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
