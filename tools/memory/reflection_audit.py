"""Audit memory reflections for actionable metadata."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Tuple

from teof._paths import repo_root

ROOT = repo_root(default=Path(__file__).resolve().parents[2])
REFLECTION_DIR = ROOT / "memory" / "reflections"
DEFAULT_OUT = ROOT / "_report" / "analysis" / "reflection-gap" / "latest.json"


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _utc_now() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc)


def _effective_since(since: datetime | None, window_days: float | None) -> datetime | None:
    if window_days is None:
        return since
    window_since = _utc_now() - timedelta(days=window_days)
    if since is None:
        return window_since
    return since if since > window_since else window_since


def _iter_reflections() -> Iterable[tuple[Path, dict]]:
    if not REFLECTION_DIR.exists():
        return []
    for path in sorted(REFLECTION_DIR.glob("reflection-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        yield path, payload


def _normalise_tags(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    tags: list[str] = []
    for item in raw:
        if isinstance(item, str):
            normalised = item.strip()
            if normalised:
                tags.append(normalised)
    return tags


def run_audit(
    since: str | None = None,
    window_days: float | None = None,
    out: Path | None = None,
) -> Tuple[dict, Path]:
    parsed_since = _parse_ts(since)
    effective_since = _effective_since(parsed_since, window_days)

    entries: list[dict] = []
    missing_plan: list[dict] = []
    missing_tags: list[dict] = []

    for path, payload in _iter_reflections():
        captured_at = payload.get("captured_at")
        captured_ts = _parse_ts(captured_at)
        if effective_since and captured_ts:
            if captured_ts < effective_since:
                continue

        plan_suggestion = payload.get("plan_suggestion")
        tags = _normalise_tags(payload.get("tags"))

        missing_plan_flag = not isinstance(plan_suggestion, str) or not plan_suggestion.strip()
        missing_tags_flag = not tags

        entry = {
            "path": str(path.relative_to(ROOT)),
            "captured_at": captured_at,
            "title": payload.get("title"),
            "plan_suggestion": plan_suggestion,
            "tags": tags,
            "missing_plan_suggestion": missing_plan_flag,
            "missing_tags": missing_tags_flag,
        }
        entries.append(entry)
        if missing_plan_flag:
            missing_plan.append(entry)
        if missing_tags_flag:
            missing_tags.append(entry)

    out_path = out if out is not None else DEFAULT_OUT
    if not out_path.is_absolute():
        out_path = ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary = {
        "generated_at": _utc_now().isoformat(timespec="seconds").replace("+00:00", "Z"),
        "since": since,
        "window_days": window_days,
        "effective_since": effective_since.isoformat(timespec="seconds").replace("+00:00", "Z") if effective_since else None,
        "total": len(entries),
        "missing_plan_suggestion": {
            "count": len(missing_plan),
            "entries": missing_plan,
        },
        "missing_tags": {
            "count": len(missing_tags),
            "entries": missing_tags,
        },
        "entries": entries,
    }
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary, out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", help="ISO timestamp filter (inclusive)")
    parser.add_argument("--window-days", type=float, help="Restrict audit to reflections captured within the last N days")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output JSON path")
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Exit with status 1 when reflections missing actionable metadata are detected",
    )
    args = parser.parse_args(argv)

    summary, out_path = run_audit(args.since, args.window_days, args.out)
    try:
        rel = out_path.relative_to(ROOT)
    except ValueError:
        rel = out_path
    print(f"wrote reflection audit → {rel}")

    if args.fail_on_missing and (
        summary["missing_plan_suggestion"]["count"] or summary["missing_tags"]["count"]
    ):
        total = summary["missing_plan_suggestion"]["count"] + summary["missing_tags"]["count"]
        print(f"::error ::reflection audit detected {total} actionable gaps")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = ["run_audit", "main"]
