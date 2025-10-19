"""Utilities for inspecting the exploratory planning lane."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Iterable, List

ROOT = Path(__file__).resolve().parents[2]
LANE_DIR = ROOT / "_plans" / "exploratory"
RECEIPTS_DIR = ROOT / "_report" / "exploratory"
DEFAULT_RECEIPT_PATH = ROOT / "_report" / "usage" / "exploratory-lane-latest.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _parse_timestamp(raw: object) -> datetime | None:
    if not isinstance(raw, str) or not raw:
        return None
    try:
        value = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    return value.replace(tzinfo=timezone.utc)


@dataclass
class ExploratoryPlan:
    plan_id: str
    path: Path
    status: str
    expires_at: datetime | None
    horizon_hours: int | None
    expired: bool
    hours_remaining: float | None
    receipts: List[str]
    receipts_root: Path

    @property
    def receipts_count(self) -> int:
        return len(self.receipts)

    @property
    def near_expiry(self) -> bool:
        if self.hours_remaining is None:
            return False
        return self.hours_remaining >= 0 and self.hours_remaining < 24


def _collect_receipts(plan_id: str, *, root: Path) -> tuple[list[str], Path]:
    receipts_root = root / "_report" / "exploratory" / plan_id
    receipts: list[str] = []
    if receipts_root.exists():
        for item in receipts_root.rglob("*"):
            if item.is_file():
                try:
                    rel = item.relative_to(root)
                except ValueError:
                    rel = item
                receipts.append(rel.as_posix())
    return sorted(receipts), receipts_root


def _classify_plan(path: Path, *, now: datetime, root: Path) -> ExploratoryPlan | None:
    payload = _read_json(path)
    if not payload:
        return None
    plan_id = payload.get("plan_id")
    if not isinstance(plan_id, str) or not plan_id:
        return None
    status = str(payload.get("status", "")).strip().lower() or "queued"
    meta = payload.get("exploratory")
    expires_raw = None
    horizon = None
    if isinstance(meta, dict):
        expires_raw = meta.get("expires_at")
        horizon_raw = meta.get("horizon_hours")
        if isinstance(horizon_raw, int):
            horizon = horizon_raw
    if expires_raw is None:
        expires_raw = payload.get("expires_at")
    expires_at = _parse_timestamp(expires_raw)
    hours_remaining: float | None = None
    expired = False
    if expires_at is not None:
        delta = expires_at - now
        hours_remaining = delta.total_seconds() / 3600.0
        expired = delta < timedelta(0)
    receipts, receipts_root = _collect_receipts(plan_id, root=root)
    return ExploratoryPlan(
        plan_id=plan_id,
        path=path,
        status=status,
        expires_at=expires_at,
        horizon_hours=horizon,
        expired=expired,
        hours_remaining=hours_remaining,
        receipts=receipts,
        receipts_root=receipts_root,
    )


def scan_lane(*, root: Path | None = None, warning_hours: float = 24.0) -> dict:
    root = root or ROOT
    lane = root / "_plans" / "exploratory"
    now = _now()
    plans: list[ExploratoryPlan] = []
    errors: list[str] = []

    if lane.exists():
        for plan_path in sorted(lane.glob("*.plan.json")):
            plan = _classify_plan(plan_path, now=now, root=root)
            if plan is None:
                errors.append(f"unable to parse {plan_path}")
                continue
            plans.append(plan)

    counts = {
        "total": len(plans),
        "expired": sum(1 for plan in plans if plan.expired),
        "active": sum(1 for plan in plans if not plan.expired and plan.status != "done"),
        "done": sum(1 for plan in plans if plan.status == "done"),
        "receipts_missing": sum(1 for plan in plans if plan.receipts_count == 0),
        "expiring": sum(
            1
            for plan in plans
            if plan.hours_remaining is not None and 0 <= plan.hours_remaining <= warning_hours
        ),
    }

    def _plan_dict(plan: ExploratoryPlan) -> dict:
        expires_iso = plan.expires_at.strftime("%Y-%m-%dT%H:%M:%SZ") if plan.expires_at else None
        return {
            "plan_id": plan.plan_id,
            "path": plan.path.relative_to(root).as_posix() if plan.path.exists() else plan.path.as_posix(),
            "status": plan.status,
            "expires_at": expires_iso,
            "hours_remaining": plan.hours_remaining,
            "expired": plan.expired,
            "horizon_hours": plan.horizon_hours,
            "receipts": plan.receipts,
            "receipts_count": plan.receipts_count,
        }

    return {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": str(root),
        "warning_hours": warning_hours,
        "counts": counts,
        "plans": [_plan_dict(plan) for plan in plans],
        "errors": errors,
    }


def _render_table(summary: dict) -> str:
    header = ["plan_id", "status", "expires_at", "hours_remaining", "receipts"]
    rows: list[list[str]] = [header]
    for plan in summary["plans"]:
        hours = plan["hours_remaining"]
        if hours is None:
            remaining = "-"
        else:
            remaining = f"{hours:.1f}"
        rows.append(
            [
                plan["plan_id"],
                plan["status"],
                plan["expires_at"] or "-",
                remaining,
                str(plan["receipts_count"]),
            ]
        )
    widths = [max(len(row[idx]) for row in rows) for idx in range(len(header))]
    lines: list[str] = []
    for idx, row in enumerate(rows):
        segment = " | ".join(cell.ljust(widths[col]) for col, cell in enumerate(row))
        lines.append(segment)
        if idx == 0:
            lines.append("-+-".join("-" * width for width in widths))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="exploratory_lane",
        description="Inspect exploratory plans and receipts",
    )
    parser.add_argument(
        "--warning-hours",
        type=float,
        default=24.0,
        help="Threshold for expiring plans in hours (default: 24)",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output style (default: table)",
    )
    parser.add_argument(
        "--out",
        help="Write JSON summary to the provided path",
    )
    parser.add_argument(
        "--receipt",
        action="store_true",
        help=f"Write JSON summary receipt to {DEFAULT_RECEIPT_PATH.relative_to(ROOT)}",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    summary = scan_lane(warning_hours=float(args.warning_hours))
    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.receipt:
        receipt_path = DEFAULT_RECEIPT_PATH
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(_render_table(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
