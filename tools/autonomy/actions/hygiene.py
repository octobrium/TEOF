"""Repo hygiene action helpers."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping


ROOT = Path(__file__).resolve().parents[3]
REPORT_SUBDIR = Path("_report") / "usage" / "autonomy-actions"


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
        "actions": {
            "chronicle_rotation": chronicle_rotation,
            "selfprompt_rotation": selfprompt_rotation,
        },
    }

    report_path = report_dir / f"hygiene-{_utc_now().strftime('%Y%m%dT%H%M%SZ')}.json"
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "report_path": report_path,
        "result": result,
    }


__all__ = ["run"]
