#!/usr/bin/env python3
"""Audit governance/anchors.json for append-only policy compliance gaps."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ANCHORS = ROOT / "governance" / "anchors.json"
REPORT_DIR = ROOT / "_report" / "usage" / "anchors"


@dataclass
class AnchorEventSummary:
    index: int
    ts: str | None
    event_type: str
    has_prev_hash: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "ts": self.ts,
            "event_type": self.event_type,
            "has_prev_content_hash": self.has_prev_hash,
        }


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc


def _event_type(event: dict[str, Any]) -> str:
    value = event.get("type")
    if isinstance(value, str) and value.strip():
        return value
    return "event"


def audit_anchors(payload: dict[str, Any]) -> dict[str, Any]:
    policy = payload.get("policy") if isinstance(payload.get("policy"), str) else None
    events = payload.get("events") if isinstance(payload.get("events"), list) else []

    summaries: list[AnchorEventSummary] = []
    missing_prev: list[int] = []
    first_missing_prev: list[int] = []

    for idx, raw in enumerate(events):
        if not isinstance(raw, dict):
            continue
        ts = raw.get("ts") if isinstance(raw.get("ts"), str) else None
        has_prev = isinstance(raw.get("prev_content_hash"), str) and bool(raw.get("prev_content_hash"))
        if not has_prev:
            if idx == 0:
                first_missing_prev.append(idx)
            else:
                missing_prev.append(idx)
        summaries.append(
            AnchorEventSummary(
                index=idx,
                ts=ts,
                event_type=_event_type(raw),
                has_prev_hash=has_prev,
            )
        )

    issues: dict[str, Any] = {}
    if policy != "append-only":
        issues["policy_mismatch"] = policy
    if missing_prev:
        issues["events_missing_prev_content_hash"] = missing_prev
    if first_missing_prev and len(events) > 1:
        issues["first_event_missing_prev_content_hash"] = first_missing_prev

    return {
        "evaluated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "policy": policy,
        "event_count": len(events),
        "event_summaries": [summary.to_dict() for summary in summaries],
        "issues": issues,
    }


def write_report(payload: dict[str, Any], *, out_dir: Path | None = None) -> Path:
    directory = out_dir or REPORT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = directory / f"anchors-audit-{timestamp}.json"
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--anchors",
        type=Path,
        default=DEFAULT_ANCHORS,
        help="Path to anchors.json (default: governance/anchors.json)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Optional directory to write the audit report (default: _report/usage/anchors)",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Print audit summary without writing a report",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    anchors_path = args.anchors
    if not anchors_path.exists():
        parser.error(f"anchors file not found: {anchors_path}")

    payload = audit_anchors(_load_json(anchors_path))

    if args.no_write:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        target = write_report(payload, out_dir=args.out)
        report_path = target.relative_to(ROOT).as_posix() if target.is_relative_to(ROOT) else target.as_posix()
        print(json.dumps({"report": report_path}, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
