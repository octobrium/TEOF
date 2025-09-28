"""CLI for logging ethics scenario receipts."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import uuid
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "_report" / "usage" / "governance"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", help="Short description of the defensive action")
    parser.add_argument(
        "--scenario",
        required=True,
        help="Playbook scenario id (e.g. disinformation, humanitarian-leverage)",
    )
    parser.add_argument(
        "--impact",
        choices=["low", "medium", "high"],
        default="medium",
        help="Impact level for disclosure planning",
    )
    parser.add_argument(
        "--actions",
        nargs="*",
        help="List of actions taken (strings)",
    )
    parser.add_argument(
        "--receipts",
        nargs="*",
        help="Related receipts already produced",
    )
    parser.add_argument(
        "--notes",
        nargs="*",
        help="Optional extended notes",
    )
    return parser.parse_args(argv)


def build_payload(args: argparse.Namespace) -> dict:
    now = dt.datetime.utcnow()
    payload = {
        "event_id": uuid.uuid4().hex,
        "generated_at": now.strftime(ISO_FMT),
        "summary": args.summary,
        "scenario": args.scenario,
        "impact": args.impact,
        "actions": args.actions or [],
        "linked_receipts": args.receipts or [],
    }
    if args.notes:
        payload["notes"] = args.notes
    return payload


def write_receipt(payload: dict) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = payload["generated_at"].replace("-", "").replace(":", "")
    path = REPORT_DIR / f"ethics-scenario-{ts}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(args)
    path = write_receipt(payload)
    rel = path.relative_to(ROOT)
    print(f"ethics scenario logged → {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
