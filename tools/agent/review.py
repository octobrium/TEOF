#!/usr/bin/env python3
"""Create review request/response receipts under `_report/reviews/`."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from tools.agent import session_guard

ROOT = Path(__file__).resolve().parents[2]
REVIEWS_DIR = ROOT / "_report" / "reviews"


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_receipt(request_id: str, payload: dict[str, object], kind: str) -> Path:
    request_dir = REVIEWS_DIR / request_id
    request_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{payload['ts']}-{kind}.json"
    path = request_dir / filename
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _resolve_agent(agent: str | None) -> str:
    return session_guard.resolve_agent_id(agent)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    req = sub.add_parser("request", help="Create a review request receipt")
    req.add_argument("--id", required=True, help="Request identifier (slug)")
    req.add_argument("--summary", required=True, help="What needs review?")
    req.add_argument("--blocking-on", help="Optional description of what this blocks")
    req.add_argument("--due", help="Optional ISO8601 due timestamp")
    req.add_argument("--agent", help="Override agent id (defaults to manifest)")
    req.add_argument("--artifact", action="append", default=[], help="Artifacts to review (repeatable)")
    req.set_defaults(func=handle_request)

    resp = sub.add_parser("respond", help="Respond to an existing review request")
    resp.add_argument("--id", required=True, help="Request identifier (slug)")
    resp.add_argument(
        "--status",
        required=True,
        choices=("approved", "changes_requested", "info"),
        help="Outcome of the review",
    )
    resp.add_argument("--notes", required=True, help="Summary of findings")
    resp.add_argument("--agent", help="Override agent id (defaults to manifest)")
    resp.add_argument("--artifact", action="append", default=[], help="Supporting artifacts (repeatable)")
    resp.set_defaults(func=handle_response)

    lst = sub.add_parser("list", help="List review requests/responses")
    lst.add_argument(
        "--status",
        choices=("pending", "closed", "all"),
        default="pending",
        help="Filter by current state (default: pending)",
    )
    lst.set_defaults(func=handle_list)

    return parser


def handle_request(args: argparse.Namespace) -> int:
    agent_id = _resolve_agent(args.agent)
    payload = {
        "ts": _iso_now(),
        "type": "request",
        "request_id": args.id,
        "requester": agent_id,
        "summary": args.summary,
        "blocking_on": args.blocking_on,
        "due": args.due,
        "artifacts": list(_clean_artifacts(args.artifact)),
        "status": "pending",
    }
    path = _write_receipt(args.id, payload, "request")
    print(f"wrote review request → {path.relative_to(ROOT)}")
    return 0


def handle_response(args: argparse.Namespace) -> int:
    agent_id = _resolve_agent(args.agent)
    payload = {
        "ts": _iso_now(),
        "type": "response",
        "request_id": args.id,
        "reviewer": agent_id,
        "status": args.status,
        "notes": args.notes,
        "artifacts": list(_clean_artifacts(args.artifact)),
    }
    path = _write_receipt(args.id, payload, "response")
    print(f"wrote review response → {path.relative_to(ROOT)}")
    return 0


def _clean_artifacts(items: Sequence[str]) -> list[str]:
    cleaned: list[str] = []
    for item in items:
        value = item.strip()
        if value:
            cleaned.append(value)
    return cleaned


def handle_list(args: argparse.Namespace) -> int:
    rows = _collect_review_states()
    filtered: list[dict[str, str]] = []
    for row in rows:
        state = row["state"]
        include = True
        if args.status == "pending":
            include = state != "approved"
        elif args.status == "closed":
            include = state == "approved"
        if include:
            filtered.append(row)
    if not filtered:
        print("(no reviews)")
        return 0
    headers = ["request_id", "state", "summary", "updated_at"]
    widths = [max(len(row[h]) for row in filtered + [dict(zip(headers, headers))]) for h in headers]
    header_line = "  ".join(h.ljust(widths[idx]) for idx, h in enumerate(headers))
    print(header_line)
    print("  ".join("-" * w for w in widths))
    for row in filtered:
        print("  ".join(row[h].ljust(widths[idx]) for idx, h in enumerate(headers)))
    return 0


def _collect_review_states() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not REVIEWS_DIR.exists():
        return rows
    for request_dir in sorted(p for p in REVIEWS_DIR.iterdir() if p.is_dir()):
        request = _latest_entry(request_dir, "request")
        if not request:
            continue
        response = _latest_entry(request_dir, "response")
        state = "pending"
        updated = request.get("ts", _iso_now())
        if response:
            state = response.get("status", "info")
            updated = response.get("ts", updated)
        rows.append(
            {
                "request_id": request_dir.name,
                "state": state,
                "summary": str(request.get("summary", "")),
                "updated_at": updated,
            }
        )
    return rows


def _latest_entry(directory: Path, entry_type: str) -> dict | None:
    entries: list[dict] = []
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if data.get("type") == entry_type:
            entries.append(data)
    if not entries:
        return None
    entries.sort(key=lambda item: item.get("ts", ""), reverse=True)
    return entries[0]


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
