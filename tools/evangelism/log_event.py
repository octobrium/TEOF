"""Log evangelism cadence events as receipts."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RECEIPT_DIR = ROOT / "_report" / "usage" / "evangelism"


def _today_iso() -> str:
    return dt.datetime.utcnow().strftime("%Y-%m-%d")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", help="Short note describing the touch or outcome")
    parser.add_argument(
        "--channel",
        required=True,
        help="Channel used (e.g. blog, social, webinar)",
    )
    parser.add_argument(
        "--arc",
        required=True,
        help="Narrative arc identifier (Arc A/B/C or custom)",
    )
    parser.add_argument(
        "--asset",
        required=True,
        help="Primary asset path referenced in the outreach",
    )
    parser.add_argument(
        "--status",
        default="scheduled",
        choices=["scheduled", "sent", "published", "follow_up"],
        help="Lifecycle status for the touch",
    )
    parser.add_argument(
        "--date",
        default=_today_iso(),
        help="Calendar date for the event (YYYY-MM-DD, default: today)",
    )
    parser.add_argument(
        "--audience",
        help="Audience segment or partner",
    )
    parser.add_argument(
        "--link",
        help="External URL or document path with the published asset",
    )
    parser.add_argument(
        "--notes",
        help="Optional extended notes (stored in receipt)",
    )
    return parser.parse_args()


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    now = dt.datetime.utcnow()
    payload: dict[str, Any] = {
        "event_id": uuid.uuid4().hex,
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "date": args.date,
        "channel": args.channel,
        "arc": args.arc,
        "asset": args.asset,
        "status": args.status,
        "summary": args.summary,
    }
    if args.audience:
        payload["audience"] = args.audience
    if args.link:
        payload["link"] = args.link
    if args.notes:
        payload["notes"] = args.notes
    return payload


def write_receipt(payload: dict[str, Any]) -> Path:
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = payload["generated_at"].replace(":", "").replace("-", "")
    path = RECEIPT_DIR / f"event-{timestamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    args = parse_args()
    payload = build_payload(args)
    path = write_receipt(payload)
    rel = path.relative_to(ROOT)
    print(f"evangelism event logged → {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
