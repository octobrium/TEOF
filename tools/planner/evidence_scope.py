#!/usr/bin/env python3
"""Evidence scope helpers shared across guards."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from tools.planner import validate as planner_validate
from tools.planner.validate import EVIDENCE_BUCKETS

ROOT = Path(__file__).resolve().parents[2]
PLANS_DIR = ROOT / "_plans"
RECEIPT_DIR = ROOT / "_report" / "usage" / "evidence-scope"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass
class EvidenceReport:
    plan_id: str
    ok: bool
    version: int
    counts: dict[str, int]
    receipts: List[str]
    errors: List[str]


def _relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _empty_counts() -> dict[str, int]:
    return {bucket: 0 for bucket in EVIDENCE_BUCKETS}


def evaluate_plan(plan_id: str, *, strict: bool = True) -> EvidenceReport:
    normalized = plan_id.strip()
    plan_path = PLANS_DIR / f"{normalized}.plan.json"
    if not plan_path.exists():
        return EvidenceReport(
            plan_id=normalized,
            ok=False,
            version=0,
            counts=_empty_counts(),
            receipts=[],
            errors=[f"plan not found: {_relative(plan_path)}"],
        )

    result = planner_validate.validate_plan(plan_path, strict=strict)
    validation_errors = list(result.errors)
    plan_data = result.plan
    if plan_data is None:
        try:
            plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            plan_data = None

    if plan_data is None:
        return EvidenceReport(
            plan_id=normalized,
            ok=False,
            version=0,
            counts=_empty_counts(),
            receipts=[],
            errors=validation_errors or ["plan validation failed"],
        )

    version = int(plan_data.get("version") or 0)
    scope = plan_data.get("evidence_scope") if isinstance(plan_data.get("evidence_scope"), dict) else {}
    counts = {bucket: len(scope.get(bucket, [])) if scope else 0 for bucket in EVIDENCE_BUCKETS}
    receipts = list(scope.get("receipts", [])) if isinstance(scope, dict) else []
    errors: List[str] = validation_errors.copy()

    if version < 1:
        errors.append("plan version < 1; re-scope with --plan-version 1 to enforce evidence coverage")
    elif not scope:
        errors.append("evidence_scope missing")
    else:
        if counts["internal"] == 0:
            errors.append("internal evidence references missing")
        if (counts["external"] + counts["comparative"]) == 0:
            errors.append("external or comparative evidence references missing")
        if not receipts:
            errors.append("evidence receipts missing (attach _report/... artifact summarizing the survey)")

    return EvidenceReport(
        plan_id=normalized,
        ok=not errors,
        version=version,
        counts=counts,
        receipts=receipts,
        errors=errors,
    )


def require_evidence(plan_ids: Iterable[str], *, strict: bool = True) -> Tuple[bool, List[EvidenceReport]]:
    seen: set[str] = set()
    reports: List[EvidenceReport] = []
    for raw in plan_ids:
        if not raw:
            continue
        normalized = raw.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        reports.append(evaluate_plan(normalized, strict=strict))
    ok = all(report.ok for report in reports) if reports else True
    return ok, reports


def scan_plans(*, plan_ids: Sequence[str] | None = None, strict: bool = True) -> List[EvidenceReport]:
    if plan_ids:
        targets = plan_ids
    else:
        targets = [path.stem.replace(".plan", "") for path in sorted(PLANS_DIR.glob("*.plan.json"))]
    _, reports = require_evidence(targets, strict=strict)
    return reports


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


def _default_receipt_dir() -> Path:
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    return RECEIPT_DIR


def write_receipt(reports: Sequence[EvidenceReport], *, receipt_dir: Path | None = None) -> Path:
    if receipt_dir is None:
        receipt_dir = _default_receipt_dir()
    else:
        receipt_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    receipt_path = receipt_dir / f"evidence-scope-{timestamp}.json"

    version_one = [report for report in reports if report.version >= 1]
    missing = [report for report in version_one if not report.ok]
    receipts_missing = [report for report in version_one if not report.receipts]
    payload = {
        "schema": "teof.evidence_scope.report/v1",
        "generated_at": _iso_now(),
        "plans_covered": len(reports),
        "version_one_plans": len(version_one),
        "version_one_missing": len(missing),
        "version_one_missing_receipts": len(receipts_missing),
        "reports": [
            {
                "plan_id": report.plan_id,
                "version": report.version,
                "counts": report.counts,
                "receipts": report.receipts,
                "errors": report.errors,
            }
            for report in reports
        ],
    }
    receipt_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    latest = receipt_dir / "latest.json"
    latest_payload = {
        "generated_at": payload["generated_at"],
        "receipt": _relative(receipt_path),
        "plans_covered": payload["plans_covered"],
        "version_one_missing": payload["version_one_missing"],
    }
    latest.write_text(json.dumps(latest_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt_path


def _print_summary(reports: Sequence[EvidenceReport]) -> None:
    payload = {
        "generated_at": _iso_now(),
        "plans": [
            {
                "plan_id": report.plan_id,
                "version": report.version,
                "counts": report.counts,
                "receipts": report.receipts,
                "ok": report.ok,
                "errors": report.errors,
            }
            for report in reports
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect evidence_scope coverage across plans")
    parser.add_argument(
        "--plan",
        action="append",
        default=[],
        help="Plan id to inspect (repeatable). When omitted, requires --all.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scan every *.plan.json under _plans/",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict validation (default: on)",
    )
    parser.add_argument(
        "--no-strict",
        dest="strict",
        action="store_false",
        help="Disable strict validation",
    )
    parser.set_defaults(strict=True)
    parser.add_argument(
        "--receipt-dir",
        help="Directory for evidence scope receipts (default: _report/usage/evidence-scope)",
    )
    parser.add_argument(
        "--no-receipt",
        action="store_true",
        help="Skip writing receipts; only print JSON summary",
    )
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Exit non-zero when any version>=1 plan fails evidence coverage",
    )
    parser.add_argument(
        "--fail-on-missing-receipts",
        action="store_true",
        help="Exit non-zero when any version>=1 plan lacks evidence receipts",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not args.plan and not args.all:
        parser.error("Provide --plan <id> (repeatable) or --all to scan every plan")

    plan_ids = args.plan if args.plan else None
    reports = scan_plans(plan_ids=plan_ids, strict=args.strict)
    _print_summary(reports)
    if not args.no_receipt:
        receipt_dir = Path(args.receipt_dir) if args.receipt_dir else None
        if receipt_dir and not receipt_dir.is_absolute():
            receipt_dir = ROOT / receipt_dir
        write_receipt(reports, receipt_dir=receipt_dir)

    version_one = [report for report in reports if report.version >= 1]
    missing = [report for report in version_one if not report.ok]
    receipts_missing = [report for report in version_one if not report.receipts]
    exit_code = 0
    if args.fail_on_missing and missing:
        print(
            f"evidence_scope: {len(missing)} plan(s) failing evidence coverage: "
            + ", ".join(report.plan_id for report in missing),
            file=sys.stderr,
        )
        exit_code = max(exit_code, 2)
    if args.fail_on_missing_receipts and receipts_missing:
        print(
            f"evidence_scope: {len(receipts_missing)} plan(s) missing evidence receipts: "
            + ", ".join(report.plan_id for report in receipts_missing),
            file=sys.stderr,
        )
        exit_code = max(exit_code, 2)

    return exit_code


__all__ = ["EvidenceReport", "evaluate_plan", "require_evidence", "scan_plans", "write_receipt"]


if __name__ == "__main__":
    raise SystemExit(main())
