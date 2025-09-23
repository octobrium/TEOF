"""Append a real-world impact entry."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[2]
IMPACT_LOG = ROOT / "memory" / "impact" / "log.jsonl"


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True, help="Outcome title")
    parser.add_argument("--value", type=float, required=True, help="Estimated value (numeric)")
    parser.add_argument("--currency", default="USD", help="Currency code (default USD)")
    parser.add_argument("--description", required=True, help="Impact description")
    parser.add_argument(
        "--receipt",
        action="append",
        default=[],
        help="Supporting receipt path (repeatable)",
    )
    parser.add_argument("--notes", help="Optional notes or follow-ups")
    parser.add_argument("--dry-run", action="store_true", help="Print entry without writing")
    return parser


def write_entry(entry: dict[str, object], *, dry_run: bool) -> None:
    if dry_run:
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        return
    impact_path = IMPACT_LOG
    impact_path.parent.mkdir(parents=True, exist_ok=True)
    with impact_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    try:
        rel = impact_path.relative_to(ROOT)
    except ValueError:
        rel = impact_path
    print(f"impact-log: appended entry -> {rel}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    entry = {
        "recorded_at": _iso_now(),
        "title": args.title,
        "value": args.value,
        "currency": args.currency,
        "description": args.description,
        "receipts": args.receipt,
        "notes": args.notes,
    }
    write_entry(entry, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
