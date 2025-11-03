"""Cadence guard for autonomy footprint pruning."""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from typing import Iterable, Mapping

from teof import status_report
from tools.autonomy.shared import load_json, utc_timestamp, write_receipt_payload

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RECEIPT_DIR = Path("_report") / "usage" / "autonomy-prune"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _receipt_dir(root: Path | None = None) -> Path:
    base = root or ROOT
    return base / DEFAULT_RECEIPT_DIR


def _parse_iso(raw: str | None) -> dt.datetime | None:
    if not raw:
        return None
    try:
        return dt.datetime.strptime(raw, ISO_FMT).replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def _load_prune_receipts(root: Path | None = None, limit: int = 10) -> list[tuple[Path, Mapping[str, object]]]:
    directory = _receipt_dir(root)
    if not directory.exists():
        return []
    entries: list[tuple[Path, Mapping[str, object]]] = []
    for path in sorted(directory.glob("*.json"))[-limit:]:
        payload = load_json(path)
        if isinstance(payload, Mapping):
            entries.append((path, payload))
    return entries


def compute_cadence(
    *,
    root: Path | None = None,
    interval_days: float = 14.0,
    receipt_threshold: int = 160,
    module_growth_threshold: int = 6,
) -> dict[str, object]:
    base = root or ROOT
    now = dt.datetime.now(dt.timezone.utc)
    metrics = status_report.get_autonomy_footprint(base)
    baseline = status_report.get_autonomy_baseline(base) or {}
    receipts = _load_prune_receipts(base, limit=25)

    last_receipt_time: dt.datetime | None = None
    last_receipt_path: str | None = None
    for path, payload in reversed(receipts):
        stamp = _parse_iso(str(payload.get("pruned_at") or payload.get("generated_at")))
        if stamp:
            last_receipt_time = stamp
            try:
                last_receipt_path = str(path.relative_to(base))
            except ValueError:
                last_receipt_path = str(path)
            break

    reasons: list[str] = []

    if metrics.get("receipt_count", 0) >= receipt_threshold:
        reasons.append(f"receipt_count >= {receipt_threshold}")

    baseline_modules = int(baseline.get("module_files", metrics.get("module_files", 0)))
    module_delta = metrics.get("module_files", 0) - baseline_modules
    if module_delta > module_growth_threshold:
        reasons.append(f"module_files Δ{module_delta} > {module_growth_threshold}")

    if last_receipt_time is None:
        reasons.append("no prior prune receipt")
    else:
        age = now - last_receipt_time
        if age.total_seconds() / 86400 > interval_days:
            reasons.append(f"last prune > {interval_days}d ago")

    prune_due = len(reasons) > 0

    if prune_due or last_receipt_time is None:
        next_deadline = now
    else:
        next_deadline = last_receipt_time + dt.timedelta(days=interval_days)

    recent = [
        {
            "path": str(path.relative_to(base)) if path.is_relative_to(base) else str(path),
            "pruned_at": str(payload.get("pruned_at") or payload.get("generated_at")),
            "receipt_count": payload.get("receipt_count"),
        }
        for path, payload in receipts
    ]

    return {
        "generated_at": utc_timestamp(),
        "metrics": metrics,
        "baseline": baseline,
        "interval_days": interval_days,
        "receipt_threshold": receipt_threshold,
        "module_growth_threshold": module_growth_threshold,
        "prune_due": prune_due,
        "due_reasons": reasons,
        "last_prune_receipt": last_receipt_path,
        "next_deadline": next_deadline.strftime(ISO_FMT),
        "recent_receipts": recent,
    }


def write_cadence_receipt(report: Mapping[str, object], *, root: Path | None = None, out_path: Path | None = None) -> Path:
    base = root or ROOT
    if out_path is None:
        timestamp = report.get("generated_at", utc_timestamp()).replace(":", "").replace("-", "")
        out_path = _receipt_dir(base) / f"cadence-{timestamp}.json"
    return write_receipt_payload(out_path, report)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval-days", type=float, default=14.0, help="Maximum days between pruning sweeps")
    parser.add_argument("--threshold", type=int, default=160, help="Receipt count threshold before forcing a prune")
    parser.add_argument(
        "--module-growth-threshold",
        type=int,
        default=6,
        help="Allowed module file growth over baseline before pruning is due",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Receipt path (default: _report/usage/autonomy-prune/cadence-<timestamp>.json)",
    )
    parser.add_argument(
        "--no-receipt",
        action="store_true",
        help="Skip writing cadence receipt (still prints summary and exit status)",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    report = compute_cadence(
        interval_days=args.interval_days,
        receipt_threshold=args.threshold,
        module_growth_threshold=args.module_growth_threshold,
    )
    summary = "prune cadence: due" if report["prune_due"] else "prune cadence: within thresholds"
    reasons = report.get("due_reasons") or []
    if reasons:
        summary += " (" + ", ".join(str(reason) for reason in reasons) + ")"
    print(summary)

    if not args.no_receipt:
        write_cadence_receipt(report, out_path=args.out)
    return 1 if report["prune_due"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
