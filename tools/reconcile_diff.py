#!/usr/bin/env python3
"""Compare two reconciliation hello packets."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List


def load_packet(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "instance_id" not in data:
        raise ValueError(f"{path} missing instance_id")
    return data


def compare_hash(name: str, left: str, right: str, diffs: List[str]) -> None:
    if left != right:
        diffs.append(f"{name} mismatch: {left} != {right}")


def compare_capabilities(left: list, right: list, diffs: List[str]) -> None:
    lset = set(left)
    rset = set(right)
    only_l = sorted(lset - rset)
    only_r = sorted(rset - lset)
    if only_l:
        diffs.append(f"capabilities only in left: {only_l}")
    if only_r:
        diffs.append(f"capabilities only in right: {only_r}")


def compare_receipts(left: dict, right: dict, diffs: List[str]) -> None:
    litems = {item["path"]: item["sha256"] for item in left.get("items", [])}
    ritems = {item["path"]: item["sha256"] for item in right.get("items", [])}

    for path, sha in litems.items():
        rsha = ritems.get(path)
        if rsha is None:
            diffs.append(f"receipt missing in right: {path}")
        elif rsha != sha:
            diffs.append(f"receipt hash mismatch for {path}: {sha} != {rsha}")
    for path in ritems:
        if path not in litems:
            diffs.append(f"receipt missing in left: {path}")

    compare_hash("receipts aggregate", left.get("aggregate"), right.get("aggregate"), diffs)


def compare_packets(left: dict, right: dict) -> List[str]:
    diffs: List[str] = []
    compare_hash("commandments_hash", left.get("commandments_hash"), right.get("commandments_hash"), diffs)
    compare_hash("anchors_hash", left.get("anchors_hash"), right.get("anchors_hash"), diffs)
    compare_capabilities(left.get("capabilities", []), right.get("capabilities", []), diffs)
    compare_receipts(left.get("receipts", {}), right.get("receipts", {}), diffs)
    return diffs


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
