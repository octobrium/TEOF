"""Compute high-level metrics for the Objectives Ledger (L2)."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
REFLECTION_DIR = ROOT / "memory" / "reflections"
CONDUCTOR_DIR = ROOT / "_report" / "usage" / "autonomy-conductor"
AUTONOMY_ACTIONS_DIR = ROOT / "_report" / "usage" / "autonomy-actions"
AUTH_PATH_JSON = ROOT / "_report" / "usage" / "external-authenticity.json"
AUTH_PATH_MD = ROOT / "_report" / "usage" / "external-authenticity.md"
EXTERNAL_SUMMARY = ROOT / "_report" / "usage" / "external-summary.json"


def _load_json(path: Path) -> Mapping[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _reflections_since(threshold: datetime) -> int:
    if not REFLECTION_DIR.exists():
        return 0
    count = 0
    for path in REFLECTION_DIR.glob("reflection-*.json"):
        data = _load_json(path)
        captured = _parse_iso(data.get("captured_at") if data else None)
        if captured and captured >= threshold:
            count += 1
    return count


def _conductor_cycles_since(threshold: datetime) -> int:
    if not CONDUCTOR_DIR.exists():
        return 0
    count = 0
    for path in CONDUCTOR_DIR.glob("conductor-*.json"):
        data = _load_json(path)
        generated = _parse_iso(data.get("generated_at") if data else None)
        if generated and generated >= threshold:
            count += 1
    return count


def _auth_status() -> Mapping[str, Any] | None:
    data = _load_json(AUTH_PATH_JSON)
    if data is None:
        return None
    overall = data.get("overall_avg_trust")
    attention = data.get("attention_feeds") or []
    return {
        "overall_avg_trust": overall,
        "attention_feeds": attention,
        "meets_minimum": isinstance(overall, (int, float)) and overall >= 0.7 and not attention,
    }


def _external_summary_recent(threshold: datetime) -> bool:
    if not EXTERNAL_SUMMARY.exists():
        return False
    mtime = datetime.fromtimestamp(EXTERNAL_SUMMARY.stat().st_mtime, tz=timezone.utc)
    return mtime >= threshold


def compute_status(window_days: float) -> Mapping[str, Any]:
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(days=window_days)
    reflections = _reflections_since(threshold)
    cycles = _conductor_cycles_since(threshold)
    auth = _auth_status()
    external_recent = _external_summary_recent(threshold)

    return {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_days": window_days,
        "objectives": {
            "O1": {
                "reflections_last_window": reflections,
                "meets_target": reflections >= 1,
            },
            "O2": {
                "autonomy_cycles_last_window": cycles,
                "meets_target": cycles >= 1,
            },
            "O5": auth,
            "O7": {
                "external_summary_recent": external_recent,
                "meets_target": external_recent,
            },
        },
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window-days", type=float, default=7.0, help="Sliding window in days")
    parser.add_argument("--out", type=Path, help="Optional path to write JSON summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    status = compute_status(window_days=args.window_days)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
