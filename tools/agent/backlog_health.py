"""Compute backlog health metrics and optionally emit replenishment receipts."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from itertools import islice
from pathlib import Path
from typing import Any, Dict, Iterable

ROOT = Path(__file__).resolve().parents[2]
NEXT_DEV_PATH = ROOT / "_plans" / "next-development.todo.json"
REPORT_DIR = ROOT / "_report" / "usage" / "backlog-health"
QUEUE_DIR = ROOT / "queue"
DEFAULT_THRESHOLD = 3
DEFAULT_CANDIDATE_LIMIT = 3


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_next_development(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"next-development todo file missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _build_pending_snapshot(items: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
    snapshot: list[Dict[str, Any]] = []
    for item in items:
        snapshot.append(
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "priority": item.get("priority"),
                "layer": item.get("layer"),
                "systemic_scale": item.get("systemic_scale"),
                "plan_suggestion": item.get("plan_suggestion"),
            }
        )
    return snapshot


def _rel_to_root(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _parse_queue_entry(path: Path) -> dict[str, Any] | None:
    identifier, _, slug = path.stem.partition("-")
    if not identifier.isdigit():
        return None
    title: str | None = None
    coordinate: str | None = None
    ocers: str | None = None
    with path.open("r", encoding="utf-8") as fh:
        for raw_line in islice(fh, 0, 32):
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#") and title is None:
                heading = line.lstrip("#").strip()
                if heading.lower().startswith("task:"):
                    title = heading.split(":", 1)[1].strip()
                else:
                    title = heading
            elif line.lower().startswith("coordinate:") and coordinate is None:
                coordinate = line.split(":", 1)[1].strip()
            elif line.lower().startswith("ocers target:") and ocers is None:
                ocers = line.split(":", 1)[1].strip()
            if title and coordinate and ocers:
                break

    return {
        "queue_id": identifier,
        "slug": slug or path.stem,
        "title": title or path.stem,
        "coordinate": coordinate,
        "ocers_target": ocers,
        "path": _rel_to_root(path),
    }


def load_queue(directory: Path, *, limit: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    if not directory.exists():
        return candidates
    for entry in sorted(directory.glob("*.md")):
        parsed = _parse_queue_entry(entry)
        if parsed:
            candidates.append(parsed)
        if len(candidates) >= limit:
            break
    return candidates


def compute_metrics(
    data: Dict[str, Any],
    *,
    threshold: int,
    queue_dir: Path,
    candidate_limit: int,
) -> Dict[str, Any]:
    items = data.get("items", []) if isinstance(data.get("items"), list) else []
    status_counter = Counter(item.get("status", "unknown") for item in items)
    pending_items = [item for item in items if item.get("status") == "pending"]
    pending_snapshot = _build_pending_snapshot(pending_items)
    pending_count = len(pending_snapshot)
    pending_threshold_breached = pending_count < threshold
    queue_candidates: list[dict[str, Any]] = []
    if pending_threshold_breached and candidate_limit > 0:
        queue_candidates = load_queue(queue_dir, limit=candidate_limit)

    updated_str = data.get("updated") if isinstance(data.get("updated"), str) else None
    updated_ts = _parse_timestamp(updated_str)
    hours_since_update: float | None = None
    if updated_ts is not None:
        hours_since_update = (datetime.now(timezone.utc) - updated_ts).total_seconds() / 3600.0

    return {
        "updated": updated_str,
        "hours_since_update": hours_since_update,
        "total_items": len(items),
        "status_counts": dict(status_counter),
        "pending_count": pending_count,
        "pending_items": pending_snapshot,
        "pending_threshold_breached": pending_threshold_breached,
        "replenishment_candidates": queue_candidates,
    }


def write_receipt(metrics: Dict[str, Any], threshold: int, output: Path | None) -> Path:
    payload = {
        "generated_at": _iso_now(),
        "threshold": threshold,
    }
    payload.update(metrics)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = payload["generated_at"].replace(":", "").replace("-", "")
    target = output or REPORT_DIR / f"backlog-health-{timestamp}.json"
    with target.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--next-development",
        type=Path,
        default=NEXT_DEV_PATH,
        help="Path to _plans/next-development.todo.json",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        help="Pending item threshold before flagging backlog depletion (default: 3)",
    )
    parser.add_argument(
        "--queue-dir",
        type=Path,
        default=QUEUE_DIR,
        help="Directory containing queue entries (default: queue/)",
    )
    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=DEFAULT_CANDIDATE_LIMIT,
        help="Maximum replenishment candidates to surface when the backlog is low (default: 3)",
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
    parser.add_argument(
        "--fail-on-breach",
        action="store_true",
        help="Exit with status 1 when the pending threshold is breached",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.threshold < 0:
        parser.error("--threshold must be zero or a positive integer")
    if args.candidate_limit < 0:
        parser.error("--candidate-limit must be zero or a positive integer")

    data = load_next_development(args.next_development)
    metrics = compute_metrics(
        data,
        threshold=args.threshold,
        queue_dir=args.queue_dir,
        candidate_limit=args.candidate_limit,
    )

    if not args.no_write:
        receipt_path = write_receipt(metrics, args.threshold, args.output)
        print(json.dumps({"receipt": _rel_to_root(receipt_path)}, indent=2))
    else:
        payload = {"generated_at": _iso_now(), "threshold": args.threshold}
        payload.update(metrics)
        print(json.dumps(payload, indent=2, sort_keys=True))

    if metrics["pending_threshold_breached"] and args.fail_on_breach:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
