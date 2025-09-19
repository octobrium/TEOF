"""Shared helpers for reconciliation packet comparison."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Sequence


def load_packet(path: Path) -> dict:
    """Load a reconciliation packet and validate minimal structure."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if "instance_id" not in data:
        raise ValueError(f"{path} missing instance_id")
    return data


def _compare_hash(name: str, left: str | None, right: str | None, diffs: List[str]) -> None:
    if left != right:
        diffs.append(f"{name} mismatch: {left} != {right}")


def _compare_capabilities(left: Sequence[str], right: Sequence[str], diffs: List[str]) -> None:
    lset = set(left)
    rset = set(right)
    only_left = sorted(lset - rset)
    only_right = sorted(rset - lset)
    if only_left:
        diffs.append(f"capabilities only in left: {only_left}")
    if only_right:
        diffs.append(f"capabilities only in right: {only_right}")


def _compare_receipts(left: dict, right: dict, diffs: List[str]) -> None:
    litems = {item["path"]: item.get("sha256") for item in left.get("items", [])}
    ritems = {item["path"]: item.get("sha256") for item in right.get("items", [])}

    for path, sha in litems.items():
        other = ritems.get(path)
        if other is None:
            diffs.append(f"receipt missing in right: {path}")
        elif other != sha:
            diffs.append(f"receipt hash mismatch for {path}: {sha} != {other}")
    for path in ritems:
        if path not in litems:
            diffs.append(f"receipt missing in left: {path}")

    _compare_hash("receipts aggregate", left.get("aggregate"), right.get("aggregate"), diffs)


def compare_packets(left: dict, right: dict) -> List[str]:
    """Return a list of human readable differences between packets."""
    diffs: List[str] = []
    _compare_hash("commandments_hash", left.get("commandments_hash"), right.get("commandments_hash"), diffs)
    _compare_hash("anchors_hash", left.get("anchors_hash"), right.get("anchors_hash"), diffs)
    _compare_capabilities(left.get("capabilities", []), right.get("capabilities", []), diffs)
    _compare_receipts(left.get("receipts", {}), right.get("receipts", {}), diffs)
    return diffs


__all__ = ["load_packet", "compare_packets"]
