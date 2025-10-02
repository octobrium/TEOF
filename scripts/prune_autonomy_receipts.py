"""Prune aged autonomy receipts to keep footprint metrics meaningful."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
USAGE_DIR = DEFAULT_ROOT / "_report" / "usage"
AUTONOMY_PREFIXES = {"autonomy-", "autonomy_"}


def _iter_receipts(root: Path) -> Iterable[Path]:
    if not USAGE_DIR.exists():
        return []
    for path in USAGE_DIR.rglob("*.json"):
        stem = path.stem.lower()
        if any(stem.startswith(prefix) for prefix in AUTONOMY_PREFIXES):
            yield path


def _mtime(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def prune(root: Path, max_age_days: float, keep_latest: int, dry_run: bool) -> dict[str, object]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    candidates = sorted(_iter_receipts(root), key=lambda p: _mtime(p))
    removed: list[str] = []
    kept: list[str] = []
    group_by_dir: dict[Path, list[Path]] = {}
    for path in candidates:
        group_by_dir.setdefault(path.parent, []).append(path)
    for directory, items in group_by_dir.items():
        if len(items) <= keep_latest:
            kept.extend(str(p.relative_to(root)) for p in items)
            continue
        aged = [p for p in items if _mtime(p) < cutoff]
        aged_to_remove = aged[:-keep_latest] if len(aged) > keep_latest else []
        for path in aged_to_remove:
            removed.append(str(path.relative_to(root)))
            if not dry_run:
                path.unlink(missing_ok=True)
        kept.extend(str(p.relative_to(root)) for p in items if str(p.relative_to(root)) not in removed)
    return {
        "cutoff": cutoff.isoformat(),
        "removed": removed,
        "kept": kept,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-age-days", type=float, default=30.0, help="Age cutoff for receipts")
    parser.add_argument("--keep-latest", type=int, default=5, help="Per-directory receipts to retain regardless of age")
    parser.add_argument("--dry-run", action="store_true", help="Report candidates without deleting")
    args = parser.parse_args(argv)
    result = prune(DEFAULT_ROOT, args.max_age_days, max(args.keep_latest, 0), args.dry_run)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
