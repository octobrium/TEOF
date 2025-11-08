#!/usr/bin/env python3
"""Summarize preflight usage receipts."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRE_DIR = ROOT / "_report" / "usage" / "preflight"
DEFAULT_WINDOW_HOURS = 24 * 7  # one week


def _iso_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _iter_receipts(since: datetime | None):
    if not PRE_DIR.exists():
        return
    for path in sorted(PRE_DIR.glob("preflight-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        ts = _parse_iso(str(data.get("ts", "")))
        if since and ts and ts < since:
            continue
        yield path, data, ts


def build_summary(window_hours: int) -> dict:
    since = None
    if window_hours > 0:
        since = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    counts: Counter[str] = Counter()
    agents: Counter[str] = Counter()
    latest_by_mode: dict[str, str] = {}
    total = 0
    for path, data, ts in _iter_receipts(since):
        mode = str(data.get("mode", "unknown")).lower()
        counts[mode] += 1
        agent = str(data.get("agent_id", "unknown"))
        agents[agent] += 1
        total += 1
        if ts:
            latest_by_mode[mode] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "generated_at": _iso_now(),
        "window_hours": window_hours,
        "total_runs": total,
        "mode_counts": dict(counts),
        "agent_counts": dict(agents),
        "latest_by_mode": latest_by_mode,
    }


def write_summary(summary: dict, output: Path | None) -> Path:
    if output is None:
        output = (PRE_DIR / "preflight-summary-latest.json")
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--window-hours",
        type=int,
        default=DEFAULT_WINDOW_HOURS,
        help=f"Lookback window in hours (default: {DEFAULT_WINDOW_HOURS})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for JSON summary (defaults to _report/usage/preflight/preflight-summary-latest.json)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_summary(max(args.window_hours, 0))
    output = write_summary(summary, args.output)
    print(json.dumps(summary, indent=2))
    print(f"wrote summary to {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
