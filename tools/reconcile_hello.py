#!/usr/bin/env python3
"""Emit a TEOF reconciliation hello packet (prototype)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMMANDMENTS = ROOT / "docs" / "commandments.md"
DEFAULT_ANCHORS = ROOT / "governance" / "anchors.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"missing file: {path}")
    return sha256_bytes(path.read_bytes())


def receipts_digest(paths: Iterable[Path]) -> dict:
    entries: List[dict] = []
    for p in sorted(set(paths)):
        if not p.exists():
            raise FileNotFoundError(f"receipt missing: {p}")
        entries.append({
            "path": str(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p),
            "sha256": sha256_file(p),
        })
    bundle = "".join(entry["sha256"] for entry in entries).encode("utf-8")
    aggregate = sha256_bytes(bundle) if entries else None
    return {"aggregate": aggregate, "items": entries}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit reconciliation hello packet")
    parser.add_argument("instance_id", help="Identifier for this TEOF instance")
    parser.add_argument(
        "--commandments",
        default=str(DEFAULT_COMMANDMENTS),
        help="Path to commandments document (default: docs/commandments.md)",
    )
    parser.add_argument(
        "--anchors",
        default=str(DEFAULT_ANCHORS),
        help="Path to anchors log (default: governance/anchors.json)",
    )
    parser.add_argument(
        "--receipt",
        action="append",
        default=[],
        help="Receipt path to include (can be repeated)",
    )
    parser.add_argument(
        "--capability",
        action="append",
        default=[],
        help="Optional capability tag (e.g., autocollab/ledger)",
    )
    parser.add_argument(
        "--output",
        default="-",
        help="Where to write the packet (default: stdout)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    commandments_path = (ROOT / args.commandments).resolve() if not os.path.isabs(args.commandments) else Path(args.commandments)
    anchors_path = (ROOT / args.anchors).resolve() if not os.path.isabs(args.anchors) else Path(args.anchors)
    receipt_paths = [((ROOT / r).resolve() if not os.path.isabs(r) else Path(r)) for r in args.receipt]

    packet = {
        "instance_id": args.instance_id,
        "generated": datetime.now(timezone.utc).isoformat(),
        "commandments_hash": sha256_file(commandments_path),
        "commandments_path": str(commandments_path.relative_to(ROOT) if commandments_path.is_relative_to(ROOT) else commandments_path),
        "anchors_hash": sha256_file(anchors_path),
        "anchors_path": str(anchors_path.relative_to(ROOT) if anchors_path.is_relative_to(ROOT) else anchors_path),
        "receipts": receipts_digest(receipt_paths),
        "capabilities": sorted(set(args.capability)),
    }

    output = json.dumps(packet, ensure_ascii=False, indent=2) + "\n"
    if args.output == "-":
        print(output, end="")
    else:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
