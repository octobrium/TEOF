"""Aggregate autonomy audit receipts into rolling digests and archive older runs."""
from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence

from tools.autonomy.shared import write_receipt_payload


ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = ROOT / "_report" / "usage" / "autonomy-audit"
DIGEST_DEFAULT = AUDIT_DIR / "summary-latest.json"
ARCHIVE_ROOT = ROOT / "_report" / "usage" / "autonomy-audit" / "archive"


ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass
class AuditEntry:
    path: Path
    generated_at: datetime
    layers: Sequence[str]
    gaps: Sequence[str]

    @property
    def rel_path(self) -> Path:
        try:
            return self.path.relative_to(ROOT)
        except ValueError:
            return self.path


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in (ISO_FMT, "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _load_entry(path: Path) -> AuditEntry | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    generated_at = _parse_timestamp(payload.get("generated_at"))
    if generated_at is None:
        return None
    layers = payload.get("layers") or []
    gaps = payload.get("gaps") or []
    layers_seq = [str(layer) for layer in layers if isinstance(layer, str)]
    gaps_seq = [str(gap) for gap in gaps if isinstance(gap, str)]
    return AuditEntry(path=path, generated_at=generated_at, layers=layers_seq, gaps=gaps_seq)


def discover_audits(audit_dir: Path) -> List[AuditEntry]:
    entries: list[AuditEntry] = []
    if not audit_dir.exists():
        return entries
    for path in sorted(audit_dir.iterdir()):
        if not path.is_file() or not path.name.endswith(".json"):
            continue
        if not path.name.startswith("audit-"):
            continue
        entry = _load_entry(path)
        if entry is not None:
            entries.append(entry)
    return sorted(entries, key=lambda item: item.generated_at)


def _stamp_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def aggregate_entries(
    entries: Sequence[AuditEntry],
    *,
    retain: int,
    window_days: int | None = None,
) -> Mapping[str, object]:
    if not entries:
        now = datetime.now(timezone.utc)
        return {
            "generated_at": now.strftime(ISO_FMT),
            "source": str(AUDIT_DIR.relative_to(ROOT)),
            "total_runs": 0,
            "window": None,
            "layers_seen": {},
            "gaps_seen": {},
            "latest_runs": [],
            "retained": [],
            "archived": {"stamp": None, "count": 0, "destination": None},
        }

    window_cutoff: datetime | None = None
    if window_days is not None and window_days > 0:
        window_cutoff = entries[-1].generated_at - timedelta(days=window_days)

    considered: list[AuditEntry] = [
        entry for entry in entries if window_cutoff is None or entry.generated_at >= window_cutoff
    ]
    if not considered:
        considered = entries[-retain:] if retain > 0 else [entries[-1]]

    total_runs = len(considered)
    layers_counter: Counter[str] = Counter()
    gaps_counter: Counter[str] = Counter()
    for entry in considered:
        layers_counter.update(entry.layers)
        gaps_counter.update(entry.gaps)

    latest_runs = [
        {
            "generated_at": item.generated_at.strftime(ISO_FMT),
            "layers": list(item.layers),
            "gaps": list(item.gaps),
        }
        for item in considered[-retain:]
    ]

    retained_entries = entries[-retain:] if retain > 0 else []
    retained_paths = [str(entry.rel_path) for entry in retained_entries]

    archivable = [entry for entry in entries if entry not in retained_entries]

    window = {
        "start": considered[0].generated_at.strftime(ISO_FMT),
        "end": considered[-1].generated_at.strftime(ISO_FMT),
    }

    summary = {
        "generated_at": datetime.now(timezone.utc).strftime(ISO_FMT),
        "source": str(AUDIT_DIR.relative_to(ROOT)),
        "total_runs": total_runs,
        "window": window,
        "layers_seen": dict(sorted(layers_counter.items())),
        "gaps_seen": dict(sorted(gaps_counter.items())),
        "latest_runs": latest_runs,
        "retained": retained_paths,
        "archived": {
            "stamp": None,
            "count": len(archivable),
            "destination": None,
        },
    }
    return summary


def archive_entries(entries: Iterable[AuditEntry], *, stamp: str, dry_run: bool) -> Path | None:
    entries = list(entries)
    if not entries:
        return None
    dest = ARCHIVE_ROOT / stamp
    if dry_run:
        return dest
    dest.mkdir(parents=True, exist_ok=True)
    archived_paths: list[str] = []
    for entry in entries:
        target = dest / entry.path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(entry.path), str(target))
        archived_paths.append(str(target.relative_to(ROOT)))

    manifest = {
        "generated_at": datetime.now(timezone.utc).strftime(ISO_FMT),
        "count": len(archived_paths),
        "paths": archived_paths,
    }
    write_receipt_payload(dest / "manifest.json", manifest)
    return dest


def write_digest(summary: Mapping[str, object], digest_path: Path, *, dry_run: bool) -> None:
    if dry_run:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return
    write_receipt_payload(digest_path, summary)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT), help="Repository root (defaults to repo root)")
    parser.add_argument("--retain", type=int, default=5, help="Number of latest receipts to keep in-place")
    parser.add_argument("--digest", type=Path, default=DIGEST_DEFAULT, help="Digest output path")
    parser.add_argument(
        "--window-days",
        type=int,
        help="Only aggregate receipts within the last N days (others archive immediately)",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Skip moving receipts into _apoptosis (still computes summary)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without writing or moving receipts")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    audit_dir = root / AUDIT_DIR.relative_to(ROOT)
    digest_path = args.digest if args.digest.is_absolute() else root / args.digest

    entries = discover_audits(audit_dir)
    summary = aggregate_entries(entries, retain=args.retain, window_days=args.window_days)

    archivable_set = []
    retain = args.retain if args.retain >= 0 else 0
    if entries and retain < len(entries):
        archivable_set = entries[:-retain] if retain > 0 else entries

    if summary["archived"]["count"] and not args.no_archive:
        stamp = _stamp_now()
        dest = archive_entries(archivable_set, stamp=stamp, dry_run=args.dry_run)
        summary["archived"]["stamp"] = stamp
        summary["archived"]["destination"] = str(dest.relative_to(root)) if dest else None
    else:
        summary["archived"]["stamp"] = None
        summary["archived"]["destination"] = None

    write_digest(summary, digest_path, dry_run=args.dry_run)

    print(
        f"autonomy_audit_digest: total_runs={summary['total_runs']} "
        f"retained={len(summary['retained'])} archived={summary['archived']['count']}"
    )
    if summary["archived"]["destination"]:
        print(f"  archived to: {summary['archived']['destination']}")
    print(f"  digest: {digest_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
