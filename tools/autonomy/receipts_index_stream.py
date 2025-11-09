#!/usr/bin/env python3
"""Stream the receipts index into hashed shards with a latest pointer."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "_report" / "usage" / "receipts-index" / "manifest.json"
DEFAULT_DEST = ROOT / "_report" / "usage" / "receipts-index" / "stream"
DEFAULT_POINTER = ROOT / "_report" / "usage" / "receipts-index" / "latest.json"
DEFAULT_MAX_ENTRIES = 500
DEFAULT_MAX_AGE_HOURS = 24
MODULE_NAME = "tools.autonomy.receipts_index_stream"
CLI_NAME = "teof receipts_stream"


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _load_json(path: Path) -> Mapping[str, object]:
    text = path.read_text(encoding="utf-8")
    return json.loads(text)


def _iter_receipt_entries(manifest_path: Path, manifest: Mapping[str, object]) -> Iterable[Mapping[str, object]]:
    base = manifest_path.parent
    paths = (manifest.get("paths") or {}).get("receipts") or []
    for rel in paths:
        rel_path = Path(rel)
        path = (base / rel_path).resolve()
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, Mapping):
                    yield payload


def _existing_manifests(dest: Path) -> list[tuple[Path, Mapping[str, object]]]:
    manifests: list[tuple[Path, Mapping[str, object]]] = []
    if not dest.exists():
        return manifests
    for manifest_path in sorted(dest.glob("*.manifest.json")):
        try:
            payload = _load_json(manifest_path)
        except (OSError, json.JSONDecodeError):
            continue
        manifests.append((manifest_path, payload))
    manifests.sort(key=lambda entry: entry[1].get("sequence", 0))
    return manifests


def _determine_resume_state(
    manifests: list[tuple[Path, Mapping[str, object]]],
    *,
    since_shard: str | None,
) -> tuple[int, str | None, str | None, int, datetime | None]:
    processed = 0
    prev_id: str | None = None
    prev_sha: str | None = None
    next_sequence = 1
    latest_ts: datetime | None = None

    if not manifests:
        return 0, None, None, 1, None

    for manifest_path, payload in manifests:
        shard_id = payload.get("shard_id")
        seq = payload.get("sequence")
        entries = int(payload.get("entries") or 0)
        processed += entries
        latest_ts = _parse_iso(payload.get("last_timestamp")) or latest_ts
        prev_id = shard_id if isinstance(shard_id, str) else prev_id
        prev_sha = payload.get("sha256") if isinstance(payload.get("sha256"), str) else prev_sha
        if isinstance(seq, int):
            next_sequence = max(next_sequence, seq + 1)
        if since_shard and shard_id == since_shard:
            break
    else:
        if since_shard:
            # since shard not found → reset to 0 so caller can rebuild.
            processed = 0
            prev_id = None
            prev_sha = None
            next_sequence = 1
    return processed, prev_id, prev_sha, next_sequence, latest_ts


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _sha256_text(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_shard(
    dest: Path,
    *,
    sequence: int,
    prev_shard: str | None,
    prev_sha: str | None,
    entries: list[Mapping[str, object]],
    manifest_path: Path,
) -> tuple[str, str, str, str | None, str | None]:
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    shard_id = f"receipts-{stamp}-{sequence:04d}"
    shard_filename = f"{shard_id}.jsonl"
    shard_path = dest / shard_filename
    manifest_file = dest / f"{shard_id}.manifest.json"

    with shard_path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False))
            handle.write("\n")

    sha256 = _sha256_text(shard_path)
    first_raw = _first_timestamp(entries)
    last_raw = _last_timestamp(entries)
    first_ts = _parse_iso(first_raw)
    last_ts = _parse_iso(last_raw)

    manifest_payload = {
        "shard_id": shard_id,
        "sequence": sequence,
        "prev_shard": prev_shard,
        "prev_sha256": prev_sha,
        "entries": len(entries),
        "first_timestamp": first_ts.strftime("%Y-%m-%dT%H:%M:%SZ") if first_ts else first_raw,
        "last_timestamp": last_ts.strftime("%Y-%m-%dT%H:%M:%SZ") if last_ts else last_raw,
        "sha256": sha256,
        "generated_at": _iso_now(),
        "source": _rel_path(manifest_path),
    }
    manifest_file.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return shard_id, sha256, shard_filename, manifest_payload["first_timestamp"], manifest_payload["last_timestamp"]


def _first_timestamp(entries: Sequence[Mapping[str, object]]) -> str | None:
    for entry in entries:
        ts = entry.get("mtime") or entry.get("generated_at")
        if isinstance(ts, str):
            return ts
    return None


def _last_timestamp(entries: Sequence[Mapping[str, object]]) -> str | None:
    for entry in reversed(entries):
        ts = entry.get("mtime") or entry.get("generated_at")
        if isinstance(ts, str):
            return ts
    return None


def _rel_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _update_pointer(pointer: Path, shard_rel_path: str, sha256: str, sequence: int) -> None:
    payload = {
        "latest": shard_rel_path,
        "sha256": sha256,
        "sequence": sequence,
        "generated_at": _iso_now(),
    }
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _format_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _emit_receipt(
    receipt_path: Path,
    *,
    manifest_path: Path,
    dest: Path,
    pointer: Path,
    pointer_payload: Mapping[str, object],
    new_entries: int,
    shards_created: int,
    latest_entry_ts: datetime | None,
    max_age_hours: float,
) -> None:
    payload = {
        "module": MODULE_NAME,
        "generated_at": _iso_now(),
        "command": CLI_NAME,
        "subcommand": "stream",
        "manifest": _rel_path(manifest_path),
        "dest": _rel_path(dest),
        "pointer": {
            "path": _rel_path(pointer),
            "latest": pointer_payload.get("latest"),
            "sha256": pointer_payload.get("sha256"),
            "sequence": pointer_payload.get("sequence"),
            "generated_at": pointer_payload.get("generated_at"),
        },
        "stats": {
            "new_entries": new_entries,
            "shards_created": shards_created,
            "max_age_hours": max_age_hours,
            "latest_entry_timestamp": _format_iso(latest_entry_ts),
        },
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cmd_stream(args: argparse.Namespace) -> int:
    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    if not manifest_path.exists():
        raise SystemExit(f"manifest not found: {manifest_path}")
    manifest = _load_json(manifest_path)
    entries_iter = _iter_receipt_entries(manifest_path, manifest)

    dest = args.dest if args.dest.is_absolute() else ROOT / args.dest
    pointer = args.pointer if args.pointer.is_absolute() else ROOT / args.pointer
    _ensure_dir(dest)

    existing = _existing_manifests(dest)
    processed, prev_id, prev_sha, next_sequence, latest_ts = _determine_resume_state(existing, since_shard=args.since_shard)

    all_entries = list(entries_iter)
    processed = min(processed, len(all_entries))
    new_entries = all_entries[processed:]

    written = 0
    shards_created = 0

    for start in range(0, len(new_entries), max(args.max_entries, 1)):
        chunk = new_entries[start : start + args.max_entries]
        if not chunk:
            continue
        shard_written = _finalise_batch(
            chunk,
            dest=dest,
            pointer=pointer,
            manifest_path=manifest_path,
            next_sequence=next_sequence,
            prev_id=prev_id,
            prev_sha=prev_sha,
            dry_run=args.dry_run,
        )
        if shard_written:
            shard_id, shard_sha, rel_path, last_ts_str = shard_written
            prev_id = shard_id if not args.dry_run else prev_id
            prev_sha = shard_sha if not args.dry_run else prev_sha
            latest_ts = _parse_iso(last_ts_str) or latest_ts
            next_sequence += 1
            shards_created += 1
            written += len(chunk)

    if written == 0:
        print("receipts stream: no new entries (up to date)")
    else:
        print(f"receipts stream: wrote {written} entries across {shards_created} shard(s)")

    latest_entry_ts = latest_ts or _latest_manifest_timestamp(existing)
    if args.max_age_hours > 0:
        if latest_entry_ts is None:
            print("receipts stream: unable to determine latest entry timestamp", flush=True)
        else:
            age_hours = (datetime.now(timezone.utc) - latest_entry_ts).total_seconds() / 3600
            if age_hours > args.max_age_hours:
                raise SystemExit(f"receipts stream stale: latest entry age {age_hours:.1f}h exceeds {args.max_age_hours}h")

    if args.receipt:
        receipt_path = args.receipt if args.receipt.is_absolute() else ROOT / args.receipt
        if not pointer.exists():
            raise SystemExit(f"cannot write receipt: pointer missing at {pointer}")
        pointer_payload = _load_json(pointer)
        _emit_receipt(
            receipt_path,
            manifest_path=manifest_path,
            dest=dest,
            pointer=pointer,
            pointer_payload=pointer_payload,
            new_entries=written,
            shards_created=shards_created,
            latest_entry_ts=latest_entry_ts,
            max_age_hours=args.max_age_hours,
        )

    return 0


def _latest_manifest_timestamp(existing: list[tuple[Path, Mapping[str, object]]]) -> datetime | None:
    if not existing:
        return None
    last = existing[-1][1]
    return _parse_iso(last.get("last_timestamp"))


def _finalise_batch(
    batch: list[Mapping[str, object]],
    *,
    dest: Path,
    pointer: Path,
    manifest_path: Path,
    next_sequence: int,
    prev_id: str | None,
    prev_sha: str | None,
    dry_run: bool,
) -> tuple[str, str, str, str | None] | None:
    if not batch:
        return None
    if dry_run:
        last_ts = _last_timestamp(batch)
        return ("dry-run", "", "", last_ts)
    shard_id, shard_sha, shard_filename, _, last_ts = _write_shard(
        dest,
        sequence=next_sequence,
        prev_shard=prev_id,
        prev_sha=prev_sha,
        entries=batch,
        manifest_path=manifest_path,
    )
    rel_path = _rel_path(dest / shard_filename)
    _update_pointer(pointer, rel_path, shard_sha, next_sequence)
    return shard_id, shard_sha, rel_path, last_ts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    stream = sub.add_parser("stream", help="Emit receipts index shards")
    stream.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="Path to receipts-index manifest.json")
    stream.add_argument("--dest", type=Path, default=DEFAULT_DEST, help="Directory for shard JSONL files")
    stream.add_argument("--pointer", type=Path, default=DEFAULT_POINTER, help="Pointer file capturing the latest shard")
    stream.add_argument("--max-entries", type=int, default=DEFAULT_MAX_ENTRIES, help="Maximum entries per shard (default: 500)")
    stream.add_argument("--since-shard", help="Optional shard id from which to resume (inclusive)")
    stream.add_argument("--max-age-hours", type=float, default=DEFAULT_MAX_AGE_HOURS, help="Fail when latest entry is older than this threshold (default: 24h)")
    stream.add_argument("--dry-run", action="store_true", help="Simulate shard creation without writing pointer updates")
    stream.add_argument("--receipt", type=Path, help="Optional JSON receipt path summarizing the stream run")
    stream.set_defaults(func=cmd_stream)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
