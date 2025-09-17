#!/usr/bin/env python3
"""Produce a reconciliation merge summary using hello packets."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Import helpers from reconcile_diff for consistency
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from reconcile_diff import compare_packets, load_packet  # type: ignore


def summarize(left_path: Path, right_path: Path) -> dict:
    left = load_packet(left_path)
    right = load_packet(right_path)
    diffs = compare_packets(left, right)
    matches = len(diffs) == 0

    summary = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "left": {
            "instance_id": left.get("instance_id"),
            "commandments_hash": left.get("commandments_hash"),
            "anchors_hash": left.get("anchors_hash"),
            "capabilities": left.get("capabilities", []),
        },
        "right": {
            "instance_id": right.get("instance_id"),
            "commandments_hash": right.get("commandments_hash"),
            "anchors_hash": right.get("anchors_hash"),
            "capabilities": right.get("capabilities", []),
        },
        "matches": matches,
        "differences": diffs,
    }

    if not matches:
        note_lines = [
            "Reconciliation Summary:",
            f"- left instance: {summary['left']['instance_id']}",
            f"- right instance: {summary['right']['instance_id']}",
        ]
        if diffs:
            note_lines.append("- observed differences:")
            note_lines.extend(f"  • {d}" for d in diffs)
        summary["anchor_note"] = "\n".join(note_lines)
    else:
        summary["anchor_note"] = (
            "Reconciliation Summary:\n"
            f"- left instance: {summary['left']['instance_id']}\n"
            f"- right instance: {summary['right']['instance_id']}\n"
            "- hashes aligned; safe to append synchronization anchor."
        )

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize reconciliation between two hello packets")
    parser.add_argument("left", help="Path to local hello packet")
    parser.add_argument("right", help="Path to peer hello packet")
    parser.add_argument("--output", default="-", help="Write summary JSON to file (default stdout)")
    args = parser.parse_args()

    summary = summarize(Path(args.left), Path(args.right))

    data = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.output == "-":
        print(data, end="")
    else:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(data, encoding="utf-8")
        print(f"wrote {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
