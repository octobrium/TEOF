#!/usr/bin/env python3
"""Fetch missing receipts based on reconcile_diff output (prototype)."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch missing receipts from a peer packet")
    parser.add_argument("source", help="Path to hello packet from peer")
    parser.add_argument("dest", help="Directory to copy missing receipts into")
    return parser.parse_args()


def copy_receipts(packet: dict, dest: Path) -> list[str]:
    missing: list[str] = []
    for item in packet.get("receipts", {}).get("items", []):
        rel = Path(item["path"])
        src = ROOT / rel
        if not src.exists():
            missing.append(f"peer receipt missing locally: {rel}")
            continue
        dest_path = dest / rel.name
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest_path)
    return missing


def main() -> int:
    args = parse_args()
    packet_path = Path(args.source)
    dest = Path(args.dest)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))

    dest.mkdir(parents=True, exist_ok=True)
    warnings = copy_receipts(packet, dest)
    if warnings:
        for msg in warnings:
            print("WARN", msg)
        return 1
    print(f"Copied {len(packet.get('receipts', {}).get('items', []))} receipts to {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
