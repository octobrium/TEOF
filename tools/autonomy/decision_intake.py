"""Capture structured decision requests."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Sequence


ROOT = Path(__file__).resolve().parents[2]
DECISION_DIR = ROOT / "memory" / "decisions"


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True, help="Decision title")
    parser.add_argument("--objective", required=True, help="Objective or desired outcome")
    parser.add_argument("--constraints", help="Constraints or guardrails (comma-separated)")
    parser.add_argument("--success-metric", help="Success metric definition")
    parser.add_argument(
        "--reference",
        action="append",
        default=[],
        help="Supporting receipt or context (repeatable)",
    )
    parser.add_argument("--tags", help="Comma-separated tags")
    parser.add_argument("--plan-id", help="Related plan id if known")
    parser.add_argument("--dry-run", action="store_true", help="Print entry without writing to disk")
    return parser


def build_record(args: argparse.Namespace) -> Dict[str, object]:
    tags = [tag.strip() for tag in (args.tags or "").split(",") if tag.strip()]
    constraints = [c.strip() for c in (args.constraints or "").split(",") if c.strip()]
    return {
        "captured_at": _iso_now(),
        "title": args.title,
        "objective": args.objective,
        "constraints": constraints,
        "success_metric": args.success_metric,
        "references": args.reference,
        "tags": tags,
        "plan_id": args.plan_id,
    }


def write_record(record: Dict[str, object], *, dry_run: bool) -> Path | None:
    if dry_run:
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return None
    DECISION_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"decision-{record['captured_at'].replace(':', '').replace('-', '')}.json"
    path = DECISION_DIR / filename
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        rel = path
    print(f"decision-intake: wrote {rel}")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    record = build_record(args)
    write_record(record, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
