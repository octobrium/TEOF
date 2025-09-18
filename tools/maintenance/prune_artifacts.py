#!/usr/bin/env python3
"""Archive stale plans and receipt artifacts into ``_apoptosis/``.

The helper scans plan + receipt directories, detects entries older than the
configured cutoff, and relocates them into ``_apoptosis/<stamp>/`` so fresh
sessions stay lean. Use ``--dry-run`` to preview the actions before applying.
"""
from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Sequence

STAMP_FORMAT = "%Y%m%dT%H%M%SZ"
DEFAULT_TARGETS = (
    "_plans",
    "_report/agent",
    "_report/manager",
    "_report/planner",
    "_report/runner",
    "_report/usage",
)
PLAN_IGNORE = {"README.md", "README", "agent-proposal-justification.md"}

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent


@dataclass(frozen=True)
class MovePlan:
    """Planned relocation from ``source`` to ``destination``."""

    source: Path
    destination: Path
    newest_mtime: datetime

    def relative_paths(self, root: Path) -> tuple[str, str]:
        return (str(self.source.relative_to(root)), str(self.destination.relative_to(root)))


def _iter_leaf_entries(base: Path) -> Iterable[Path]:
    if not base.exists():
        return
    if base.name == "_plans":
        for entry in sorted(base.iterdir()):
            if entry.name in PLAN_IGNORE:
                continue
            if entry.is_file():
                yield entry
        return

    for child in sorted(base.iterdir()):
        if child.is_file():
            yield child
            continue
        if not child.is_dir():
            continue
        for entry in sorted(child.iterdir()):
            yield entry


def _newest_mtime(path: Path) -> datetime:
    try:
        latest = path.stat().st_mtime
    except FileNotFoundError:
        return datetime.fromtimestamp(0, tz=timezone.utc)

    if path.is_file():
        return datetime.fromtimestamp(latest, tz=timezone.utc)

    max_mtime = latest
    for sub in path.rglob("*"):
        try:
            mtime = sub.stat().st_mtime
        except FileNotFoundError:
            continue
        if mtime > max_mtime:
            max_mtime = mtime
    return datetime.fromtimestamp(max_mtime, tz=timezone.utc)


def discover_moves(
    root: Path,
    targets: Sequence[str],
    cutoff: datetime,
    stamp: str,
) -> list[MovePlan]:
    moves: list[MovePlan] = []
    apoptosis_root = root / "_apoptosis" / stamp

    for rel in targets:
        base = root / rel
        if not base.exists():
            continue
        for entry in _iter_leaf_entries(base):
            latest = _newest_mtime(entry)
            if latest > cutoff:
                continue
            try:
                rel_source = entry.relative_to(root)
            except ValueError:
                # Entry outside the repo root; skip defensively.
                continue
            dest = apoptosis_root / rel_source
            moves.append(MovePlan(entry, dest, latest))
    return moves


def execute_moves(moves: Sequence[MovePlan], dry_run: bool) -> None:
    for move in moves:
        dest_parent = move.destination.parent
        if dry_run:
            continue
        dest_parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(move.source), str(move.destination))


def prune_artifacts(
    *,
    root: Path = ROOT,
    targets: Sequence[str] = DEFAULT_TARGETS,
    cutoff_hours: float = 72.0,
    dry_run: bool = False,
    stamp: str | None = None,
) -> list[MovePlan]:
    if stamp is None:
        stamp = datetime.now(timezone.utc).strftime(STAMP_FORMAT)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=cutoff_hours)
    moves = discover_moves(root, targets, cutoff, stamp)
    execute_moves(moves, dry_run)
    return moves


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Archive stale plan + receipt artifacts")
    parser.add_argument(
        "--root",
        default=str(ROOT),
        help="Repository root (defaults to script location)",
    )
    parser.add_argument(
        "--cutoff-hours",
        type=float,
        default=72.0,
        help="Age threshold in hours; artifacts older than this move to _apoptosis",
    )
    parser.add_argument(
        "--target",
        action="append",
        dest="targets",
        help="Relative directory to scan (repeatable). Defaults cover plans + reports.",
    )
    parser.add_argument(
        "--stamp",
        help="Override destination timestamp (UTC, default now)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without moving files",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    targets = tuple(args.targets) if args.targets else DEFAULT_TARGETS
    stamp = args.stamp or datetime.now(timezone.utc).strftime(STAMP_FORMAT)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=args.cutoff_hours)
    moves = discover_moves(root, targets, cutoff, stamp)

    if not moves:
        print("No stale artifacts found; nothing to prune.")
        return 0

    for move in moves:
        src_rel, dst_rel = move.relative_paths(root)
        prefix = "DRY" if args.dry_run else "MOVE"
        print(f"{prefix}: {src_rel} -> {dst_rel}")

    if not args.dry_run:
        execute_moves(moves, dry_run=False)
        print(f"Archived {len(moves)} artifact(s) into _apoptosis/{stamp}.")
    else:
        print(f"Dry-run complete; {len(moves)} artifact(s) would move to _apoptosis/{stamp}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
