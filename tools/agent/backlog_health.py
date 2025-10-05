"""Compute backlog health metrics and optionally emit receipts."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
NEXT_DEV_PATH = ROOT / "_plans" / "next-development.todo.json"
REPORT_DIR = ROOT / "_report" / "usage" / "backlog-health"
DEFAULT_THRESHOLD = 3


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_next_development(path: Path = NEXT_DEV_PATH) -> Dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"next-development todo file missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc


def compute_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    items = data.get("items", []) if isinstance(data.get("items"), list) else []
    status_counter = Counter(item.get("status", "unknown") for item in items)
    pending_items = [item for item in items if item.get("status") == "pending"]

    pending_snapshot = [
        {
            "id": item.get("id"),
            "title": item.get("title"),
            "priority": item.get("priority"),
            "layer": item.get("layer"),
            "systemic_scale": item.get("systemic_scale"),
            "plan_suggestion": item.get("plan_suggestion"),
        }
        for item in pending_items
    ]

    return {
        "updated": data.get("updated"),
        "total_items": len(items),
        "status_counts": dict(status_counter),
        "pending_items": pending_snapshot,
    }


def write_receipt(metrics: Dict[str, Any], threshold: int, output: Path | None) -> Path:
    payload = {
        "generated_at": _iso_now(),
        "threshold": threshold,
        "pending_threshold_breached": len(metrics.get("pending_items", [])) < threshold,
    }
    payload.update(metrics)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    target = output or REPORT_DIR / f"backlog-health-{payload['generated_at'].replace(':', '').replace('-', '')}.json"
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        help="Pending item threshold before flagging backlog depletion (default: 3)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional receipt path (defaults to _report/usage/backlog-health/backlog-health-<UTC>.json)",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Skip writing a receipt (still prints metrics to stdout)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    data = load_next_development()
    metrics = compute_metrics(data)

    if not args.no_write:
        receipt_path = write_receipt(metrics, args.threshold, args.output)
        print(json.dumps({"receipt": receipt_path.relative_to(ROOT).as_posix()}, indent=2))
    else:
        payload = {
            "generated_at": _iso_now(),
            "threshold": args.threshold,
            "pending_threshold_breached": len(metrics.get("pending_items", [])) < args.threshold,
        }
        payload.update(metrics)
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
