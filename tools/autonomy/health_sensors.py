"""Emit health metrics for autonomy backlog synthesis."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping

from tools.autonomy.shared import load_json

ROOT = Path(__file__).resolve().parents[2]
SUMMARY_PATH = ROOT / "_report" / "usage" / "external-summary.json"
HYGIENE_GLOB = "_report/usage/autonomy-actions/hygiene-*.json"
OUTPUT_DIR = ROOT / "_report" / "health"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _authenticity_signal() -> Mapping[str, object]:
    raw = load_json(SUMMARY_PATH)
    summary = raw if isinstance(raw, Mapping) else None
    attention_count = 0
    if summary and isinstance(summary.get("feeds"), dict):
        for feed in summary["feeds"].values():
            if isinstance(feed, dict) and feed.get("trust", {}).get("status") == "attention":
                attention_count += 1
    return {
        "source": str(SUMMARY_PATH.relative_to(ROOT)),
        "attention_feeds": attention_count,
    }


def _latest_hygiene() -> Mapping[str, object] | None:
    reports: List[Path] = sorted(ROOT.glob(HYGIENE_GLOB))
    if not reports:
        return None
    latest = reports[-1]
    raw = load_json(latest)
    data = raw if isinstance(raw, Mapping) else None
    if data is None:
        return None
    data = dict(data)
    data["report_path"] = str(latest.relative_to(ROOT))
    return data


def emit_health_report() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload: Dict[str, object] = {
        "generated_at": _iso_now(),
        "authenticity": _authenticity_signal(),
        "hygiene": _latest_hygiene(),
    }
    path = OUTPUT_DIR / f"health-{_utc_now().strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


__all__ = ["emit_health_report"]
