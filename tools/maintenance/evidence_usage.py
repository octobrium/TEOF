#!/usr/bin/env python3
"""Report evidence-of-use gaps across receipts and plans.

This helper consumes the receipts index (shared with ``tools.agent.receipts_index``)
and surfaces artifacts that no longer have referring plans as well as plans
whose declared receipts have drifted. Use it before pruning or archival sweeps
to confirm that the repo keeps only receipts with living provenance.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.agent import receipts_index

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "_report" / "usage" / "evidence-usage.json"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalise_category(value: str | None) -> str:
    return value if value else "uncategorised"


def analyse_index(
    entries: Sequence[Mapping[str, Any]],
    *,
    orphan_limit: int = 20,
) -> dict[str, Any]:
    """Return evidence-of-use summary derived from the receipts index."""

    orphan_receipts: list[dict[str, Any]] = []
    plan_failures: list[dict[str, Any]] = []
    categories: Counter[str] = Counter()

    for entry in entries:
        kind = entry.get("kind")
        if kind == "receipt":
            refs = entry.get("referenced_by") or []
            if refs:
                continue
            category = _normalise_category(entry.get("category"))
            categories[category] += 1
            orphan_receipts.append(
                {
                    "path": entry.get("path"),
                    "category": category,
                    "size": entry.get("size"),
                    "mtime": entry.get("mtime"),
                    "sha256": entry.get("sha256"),
                }
            )
        elif kind == "plan":
            missing = entry.get("missing_receipts") or []
            if not missing:
                continue
            plan_failures.append(
                {
                    "plan_id": entry.get("plan_id"),
                    "path": entry.get("path"),
                    "missing_receipts": sorted(set(missing)),
                    "status": entry.get("status"),
                    "checkpoint_status": entry.get("checkpoint_status"),
                }
            )

    orphan_receipts.sort(key=lambda item: (item.get("mtime") or "", item.get("path") or ""), reverse=True)
    plan_failures.sort(key=lambda item: (item.get("plan_id") or ""))

    summary = {
        "generated_at": _utc_timestamp(),
        "orphan_receipts": len(orphan_receipts),
        "plans_missing_receipts": len(plan_failures),
        "orphan_by_category": dict(sorted(categories.items(), key=lambda pair: pair[0])),
    }

    return {
        "summary": summary,
        "orphans": orphan_receipts[: max(orphan_limit, 0)],
        "plan_failures": plan_failures,
    }


def _build_index(root: Path) -> list[Mapping[str, Any]]:
    tracked = receipts_index._git_tracked_paths(root)  # type: ignore[attr-defined]
    return receipts_index.build_index(root, tracked=tracked)


def _print_table(report: Mapping[str, Any]) -> None:
    summary = report["summary"]
    print("Evidence-of-use summary")
    print(f"- generated_at: {summary['generated_at']}")
    print(f"- orphan_receipts: {summary['orphan_receipts']}")
    print(f"- plans_missing_receipts: {summary['plans_missing_receipts']}")
    if summary["orphan_by_category"]:
        print("- orphan_by_category:")
        for category, count in summary["orphan_by_category"].items():
            print(f"  * {category}: {count}")

    if report["orphans"]:
        print("\nTop orphan receipts:")
        for item in report["orphans"]:
            print(f"- {item['path']} (category={item['category']}, mtime={item['mtime']})")

    if report["plan_failures"]:
        print("\nPlans with missing receipts:")
        for plan in report["plan_failures"]:
            missing = ", ".join(plan["missing_receipts"])
            print(f"- {plan['plan_id']} ({plan['status']}): {missing}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Number of orphan receipts to show (default: 20)",
    )
    parser.add_argument(
        "--json",
        dest="json_path",
        help="Optional output path for JSON report (relative paths land under _report/usage/)",
    )
    parser.add_argument(
        "--root",
        default=str(ROOT),
        help=argparse.SUPPRESS,
    )
    return parser


def resolve_output(path: str | None, *, root: Path) -> Path | None:
    if path is None:
        return None
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return (DEFAULT_OUTPUT.parent / candidate).resolve()


def write_report(report: Mapping[str, Any], output: Path | None) -> None:
    if output is None:
        _print_table(report)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote evidence report to {output}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    index_entries = _build_index(root)
    report = analyse_index(index_entries, orphan_limit=args.limit)
    output = resolve_output(args.json_path, root=root)
    write_report(report, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
