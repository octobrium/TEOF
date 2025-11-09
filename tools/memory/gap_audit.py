"""Audit plans missing memory log coverage."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Sequence, Tuple

from teof._paths import repo_root

ROOT = repo_root(default=Path(__file__).resolve().parents[2])
MEMORY_LOG = ROOT / "memory" / "log.jsonl"
PLANS_DIR = ROOT / "_plans"
DEFAULT_OUT = ROOT / "_report" / "analysis" / "memory-gap" / "latest.json"


def _load_memory_refs(path: Path) -> tuple[set[str], set[str]]:
    refs: set[str] = set()
    artifacts: set[str] = set()
    if not path.exists():
        return refs, artifacts
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        ref = payload.get("ref")
        if isinstance(ref, str):
            refs.add(ref.strip())
        for artifact in payload.get("artifacts") or []:
            if isinstance(artifact, str):
                artifacts.add(artifact.strip())
    return refs, artifacts


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _collect_plan_receipts(plan: dict) -> set[str]:
    receipts: set[str] = set()
    for path in plan.get("receipts") or []:
        if isinstance(path, str):
            receipts.add(path.strip())
    for step in plan.get("steps") or []:
        if not isinstance(step, dict):
            continue
        for path in step.get("receipts") or []:
            if isinstance(path, str):
                receipts.add(path.strip())
    return receipts


def _iter_plans(since: datetime | None, plan_filter: set[str]) -> Iterable[tuple[str, Path, dict]]:
    for path in sorted(PLANS_DIR.glob("*.plan.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        plan_id = payload.get("plan_id")
        if not isinstance(plan_id, str):
            continue
        if plan_filter and plan_id not in plan_filter:
            continue
        created = _parse_ts(payload.get("created"))
        if since and created and created < since:
            continue
        yield plan_id, path, payload


def _audit(plans: Iterable[tuple[str, Path, dict]], refs: set[str], artifacts: set[str]) -> list[dict]:
    rows: list[dict] = []
    for plan_id, path, payload in plans:
        receipts = _collect_plan_receipts(payload)
        recorded = f"plan:{plan_id}" in refs or any(r in artifacts for r in receipts)
        rows.append(
            {
                "plan_id": plan_id,
                "plan_path": str(path.relative_to(ROOT)),
                "created": payload.get("created"),
                "status": payload.get("status"),
                "recorded": recorded,
                "missing_receipts": sorted(r for r in receipts if r not in artifacts),
            }
        )
    return rows


def _effective_since(since: datetime | None, window_hours: float | None) -> tuple[datetime | None, float | None]:
    if window_hours is None:
        return since, window_hours
    window_since = datetime.utcnow() - timedelta(hours=window_hours)
    if since is None:
        return window_since, window_hours
    return max(since, window_since), window_hours


def run_audit(
    since: str | None,
    window_hours: float | None = None,
    plans: Sequence[str] | None = None,
    out: Path | None = None,
) -> Tuple[dict, Path]:
    parsed_since = _parse_ts(since)
    effective_since, effective_window = _effective_since(parsed_since, window_hours)
    plan_filter = {p.strip() for p in (plans or []) if isinstance(p, str) and p.strip()}

    out_path = out if out is not None else DEFAULT_OUT
    if not out_path.is_absolute():
        out_path = ROOT / out_path

    refs, artifacts = _load_memory_refs(MEMORY_LOG)
    plan_entries = list(_iter_plans(effective_since, plan_filter))
    rows = _audit(plan_entries, refs, artifacts)
    summary = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "since": since,
        "window_hours": effective_window,
        "effective_since": effective_since.isoformat(timespec="seconds") + "Z" if effective_since else None,
        "total": len(rows),
        "recorded": sum(1 for row in rows if row["recorded"]),
        "missing": [row for row in rows if not row["recorded"]],
        "entries": rows,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary, out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", help="ISO timestamp filter (inclusive)")
    parser.add_argument(
        "--window-hours",
        type=float,
        help="Restrict audit to plans created within the last N hours",
    )
    parser.add_argument("--plan", dest="plans", action="append", help="Plan id filter (repeatable)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output JSON path")
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Exit with status 1 when plans missing memory coverage are detected",
    )
    args = parser.parse_args(argv)

    summary, out_path = run_audit(args.since, args.window_hours, args.plans, args.out)
    try:
        rel = out_path.relative_to(ROOT)
    except ValueError:
        rel = out_path
    print(f"wrote audit → {rel}")
    if args.fail_on_missing and summary["missing"]:
        count = len(summary["missing"])
        print(f"::error ::memory gap audit detected {count} missing plan entries")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = ["run_audit", "main"]
