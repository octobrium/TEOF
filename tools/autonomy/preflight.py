"""Aggregate preflight checks for autonomy runs."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Iterable

from tools.autonomy import critic, ethics_gate, frontier, objectives_status, tms

ROOT = Path(__file__).resolve().parents[2]
AUTH_JSON = ROOT / "_report" / "usage" / "external-authenticity.json"
STATUS_PATH = ROOT / "_report" / "planner" / "validate" / "summary-latest.json"
DEFAULT_RECEIPT_DIR = ROOT / "_report" / "usage" / "autonomy-preflight"


def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def gather_snapshot(*, frontier_limit: int = 5, objectives_window_days: float = 7.0) -> dict:
    authenticity = _load_json(AUTH_JSON)
    planner_status = _load_json(STATUS_PATH)
    objectives = objectives_status.compute_status(window_days=objectives_window_days)
    frontier_preview = []
    try:
        frontier_preview = [entry.as_dict() for entry in frontier.compute_frontier(limit=max(0, frontier_limit))]
    except Exception:
        frontier_preview = []
    critic_alerts = critic.detect_anomalies()
    tms_conflicts = tms.detect_conflicts()
    ethics_violations = ethics_gate.detect_violations()
    return {
        "generated_at": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authenticity": authenticity,
        "planner_status": planner_status,
        "objectives": objectives,
        "frontier_preview": frontier_preview,
        "critic_alerts": critic_alerts,
        "tms_conflicts": tms_conflicts,
        "ethics_violations": ethics_violations,
    }


def write_receipt(snapshot: dict, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Receipt path (default: _report/usage/autonomy-preflight/preflight-<UTC>.json)")
    parser.add_argument("--frontier-limit", type=int, default=5, help="Number of frontier items to include")
    parser.add_argument("--objectives-window", type=float, default=7.0, help="Window in days for objectives snapshot")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    snapshot = gather_snapshot(frontier_limit=args.frontier_limit, objectives_window_days=args.objectives_window)
    timestamp = snapshot["generated_at"].replace(":", "").replace("-", "")
    out_path = args.out or (DEFAULT_RECEIPT_DIR / f"preflight-{timestamp}.json")
    write_receipt(snapshot, out_path)
    try:
        rel = out_path.relative_to(ROOT)
    except ValueError:
        rel = out_path
    print(f"preflight: wrote receipt → {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
