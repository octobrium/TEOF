"""Helpers for loading planner queue warnings from validation summaries."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
SUMMARY_DIR = Path("_report") / "planner" / "validate"


def _load_json(path: Path) -> Dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def _discover_latest(summary_dir: Path) -> Path | None:
    latest = summary_dir / "summary-latest.json"
    if latest.exists():
        return latest
    candidates = sorted(summary_dir.glob("summary-*.json"))
    if candidates:
        return candidates[-1]
    return None


def load_summary(root: Path = ROOT) -> Dict[str, Any] | None:
    summary_dir = root / SUMMARY_DIR
    summary_path = _discover_latest(summary_dir)
    if summary_path is None:
        return None
    return _load_json(summary_path)


def extract_queue_warnings(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    warnings: List[Dict[str, Any]] = []
    generated_at = summary.get("generated_at")
    for entry in summary.get("plans", []):
        if not isinstance(entry, dict):
            continue
        plan_id = entry.get("plan_id") or entry.get("path")
        queue_payload = entry.get("queue_warnings", [])
        if isinstance(queue_payload, list):
            for warning in queue_payload:
                if isinstance(warning, dict):
                    data = dict(warning)
                    data.setdefault("plan_id", plan_id)
                    if generated_at:
                        data.setdefault("generated_at", generated_at)
                    warnings.append(data)
                elif isinstance(warning, str):
                    warnings.append(
                        {
                            "plan_id": plan_id,
                            "message": warning,
                            "generated_at": generated_at,
                        }
                    )
    return warnings


def load_queue_warnings(root: Path = ROOT) -> List[Dict[str, Any]]:
    summary = load_summary(root)
    if not summary:
        return []
    return extract_queue_warnings(summary)


__all__ = ["load_summary", "extract_queue_warnings", "load_queue_warnings"]
