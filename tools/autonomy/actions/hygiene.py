"""Repo hygiene action helpers."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Mapping, Sequence

from tools.maintenance import prune_artifacts


ROOT = Path(__file__).resolve().parents[3]
REPORT_SUBDIR = Path("_report") / "usage" / "autonomy-actions"
DEFAULT_PRUNE_TARGETS: Sequence[str] = (
    "_report/agent",
    "_report/manager",
    "_report/planner",
    "_report/runner",
    "_report/usage",
)


def _serialize_moves(root: Path, moves: Sequence[prune_artifacts.MovePlan]) -> List[Dict[str, str]]:
    serialised: List[Dict[str, str]] = []
    for move in moves:
        src_rel, dst_rel = move.relative_paths(root)
        serialised.append(
            {
                "source": src_rel,
                "destination": dst_rel,
                "newest_mtime": move.newest_mtime.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )
    return serialised


@dataclass
class DirectoryInfo:
    path: Path
    size_bytes: int
    file_count: int


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _dir_size(path: Path) -> DirectoryInfo:
    total = 0
    count = 0
    if path.exists():
        for child in path.rglob("*"):
            try:
                if child.is_file():
                    total += child.stat().st_size
                    count += 1
            except OSError:
                continue
    return DirectoryInfo(path=path, size_bytes=total, file_count=count)


def _rotate_keep_latest(
    directory: Path, keep: int, *, dry_run: bool, root: Path
) -> Dict[str, List[str]]:
    removed: List[str] = []
    if not directory.exists():
        return {"removed": removed}
    entries = sorted(
        (child for child in directory.iterdir() if child.is_file()),
        key=lambda p: p.name,
        reverse=True,
    )
    for entry in entries[keep:]:
        try:
            rel_entry = entry.relative_to(root)
        except ValueError:
            rel_entry = entry
        removed.append(str(rel_entry))
        if not dry_run:
            try:
                entry.unlink()
            except OSError:
                continue
    return {"removed": removed}


def run(
    *,
    root: Path | None = None,
    dry_run: bool = True,
    keep_chronicle: int = 5,
    keep_selfprompt: int = 10,
    prune_cutoff_hours: float = 72.0,
    prune_targets: Sequence[str] | None = None,
) -> dict:
    """Generate hygiene report and optionally prune historical artifacts."""

    root = root or ROOT
    report_dir = root / REPORT_SUBDIR
    report_dir.mkdir(parents=True, exist_ok=True)

    targets = {
        "report_usage": _dir_size(root / "_report" / "usage"),
        "report_agent": _dir_size(root / "_report" / "agent"),
        "artifacts": _dir_size(root / "artifacts"),
        "apoptosis": _dir_size(root / "_apoptosis"),
    }

    chronicle_dir = root / "_report" / "usage" / "chronicle"
    selfprompt_dir = root / "_report" / "usage" / "selfprompt"

    chronicle_rotation = _rotate_keep_latest(
        chronicle_dir, keep=keep_chronicle, dry_run=dry_run, root=root
    )
    selfprompt_rotation = _rotate_keep_latest(
        selfprompt_dir, keep=keep_selfprompt, dry_run=dry_run, root=root
    )

    prune_summary: Dict[str, object] | None = None
    if prune_cutoff_hours is not None and prune_cutoff_hours > 0:
        stamp = datetime.now(timezone.utc).strftime(prune_artifacts.STAMP_FORMAT)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=prune_cutoff_hours)
        targets_to_scan = (
            tuple(prune_targets)
            if prune_targets is not None
            else tuple(DEFAULT_PRUNE_TARGETS)
        )
        moves = prune_artifacts.discover_moves(root, targets_to_scan, cutoff, stamp)
        if not dry_run and moves:
            prune_artifacts.execute_moves(moves, dry_run=False)
        prune_summary = {
            "stamp": stamp,
            "cutoff_hours": prune_cutoff_hours,
            "targets": list(targets_to_scan),
            "moves": _serialize_moves(root, moves),
            "executed": not dry_run and bool(moves),
        }

    actions: Dict[str, object] = {
        "chronicle_rotation": chronicle_rotation,
        "selfprompt_rotation": selfprompt_rotation,
    }
    if prune_summary is not None:
        actions["prune"] = prune_summary

    result: Mapping[str, object] = {
        "generated_at": _iso_now(),
        "dry_run": dry_run,
        "targets": {
            name: {
                "size_bytes": info.size_bytes,
                "size_mb": round(info.size_bytes / (1024 * 1024), 3),
                "file_count": info.file_count,
                "path": str(info.path.relative_to(root)),
            }
            for name, info in targets.items()
        },
        "actions": actions,
    }

    report_path = report_dir / f"hygiene-{_utc_now().strftime('%Y%m%dT%H%M%SZ')}.json"
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "report_path": report_path,
        "result": result,
    }


__all__ = ["run"]
