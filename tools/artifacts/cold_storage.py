#!/usr/bin/env python3
"""Legacy artifact cold storage snapshot/restore tooling."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import shutil
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import zstandard

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = ROOT / "artifacts" / "legacy_cold_storage"
DEFAULT_RECEIPT_DIR = ROOT / "_report" / "usage" / "legacy-cold-storage"
DEFAULT_POINTER_PATH = DEFAULT_RECEIPT_DIR / "latest.json"
DEFAULT_HISTORY_PATH = DEFAULT_RECEIPT_DIR / "history.jsonl"
DEFAULT_RAW_DIRS = (
    ROOT / "_report" / "legacy_loop_out",
    ROOT / "_apoptosis",
)
DEFAULT_SHASUM_NAME = "SHASUMS.txt"
DEFAULT_MANIFEST_NAME = "manifest.json"
DEFAULT_BUNDLE_NAME = "bundle.tar.zst"
SNAPSHOT_PREFIX = "legacy-"


class ColdStorageError(RuntimeError):
    """Raised when cold storage operations cannot complete."""


@dataclass(frozen=True)
class SnapshotResult:
    snapshot_id: str
    manifest_path: Path
    bundle_path: Path
    receipt_path: Path
    pointer_path: Path


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _timestamp_token(when: dt.datetime | None = None) -> str:
    when = when or _utc_now()
    return when.strftime("%Y%m%dT%H%M%SZ")


def _timestamp_iso(when: dt.datetime | None = None) -> str:
    when = when or _utc_now()
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_rev() -> str:
    try:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
    except OSError:
        return "unknown"
    output = (result.stdout or "").strip()
    return output or "unknown"


def _abs(path: Path | str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    return candidate.resolve()


def _ensure_repo_path(path: Path) -> Path:
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise ColdStorageError(f"path must live inside repository: {path}") from exc
    return path


def _rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _iter_files(source: Path) -> Iterable[Path]:
    for entry in sorted(source.rglob("*")):
        if entry.is_file() or entry.is_symlink():
            yield entry


def _hash_file(path: Path) -> tuple[str, int]:
    if path.is_symlink():
        target = os.readlink(path)
        data = target.encode("utf-8")
        return hashlib.sha256(data).hexdigest(), len(data)

    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


class _HashingWriter:
    """Wrap a writable handle so we can hash compressed bytes while streaming."""

    def __init__(self, handle: io.BufferedWriter, hasher: "hashlib._Hash") -> None:
        self._handle = handle
        self._hasher = hasher

    def write(self, data: bytes) -> int:
        self._hasher.update(data)
        return self._handle.write(data)

    def flush(self) -> None:
        self._handle.flush()


def _bundle_snapshot(sources: Sequence[Path], bundle_path: Path) -> str:
    hasher = hashlib.sha256()
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    compressor = zstandard.ZstdCompressor(level=10)
    with bundle_path.open("wb") as raw_handle:
        writer = _HashingWriter(raw_handle, hasher)
        with compressor.stream_writer(writer) as stream:
            with tarfile.open(fileobj=stream, mode="w|") as archive:
                for source in sources:
                    archive.add(source, arcname=_rel(source), recursive=True)
    return hasher.hexdigest()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _shasums_path(snapshot_dir: Path) -> Path:
    return snapshot_dir / DEFAULT_SHASUM_NAME


def _manifest_path(snapshot_dir: Path) -> Path:
    return snapshot_dir / DEFAULT_MANIFEST_NAME


def _bundle_path(snapshot_dir: Path) -> Path:
    return snapshot_dir / DEFAULT_BUNDLE_NAME


def snapshot(
    *,
    sources: Sequence[Path],
    out_dir: Path | None = None,
    receipt_dir: Path | None = None,
    keep_source: bool = False,
    notes: str | None = None,
) -> SnapshotResult:
    if not sources:
        raise ColdStorageError("at least one --source path is required")

    resolved_sources: list[Path] = []
    for raw in sources:
        resolved = _ensure_repo_path(_abs(raw))
        if not resolved.exists():
            raise ColdStorageError(f"source missing: {_rel(resolved)}")
        if not resolved.is_dir():
            raise ColdStorageError(f"source must be a directory: {_rel(resolved)}")
        resolved_sources.append(resolved)

    out_dir = _ensure_repo_path(_abs(out_dir or DEFAULT_OUT_DIR))
    receipt_dir = _ensure_repo_path(_abs(receipt_dir or DEFAULT_RECEIPT_DIR))
    out_dir.mkdir(parents=True, exist_ok=True)
    receipt_dir.mkdir(parents=True, exist_ok=True)

    now = _utc_now()
    stamp_token = _timestamp_token(now)
    snapshot_id = f"{SNAPSHOT_PREFIX}{stamp_token}"
    snapshot_dir = out_dir / snapshot_id
    suffix = 1
    while snapshot_dir.exists():
        snapshot_dir = out_dir / f"{snapshot_id}-{suffix}"
        suffix += 1
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    file_hashes: dict[str, str] = {}
    file_count = 0
    total_bytes = 0
    for source in resolved_sources:
        for entry in _iter_files(source):
            digest, size = _hash_file(entry)
            file_hashes[_rel(entry)] = digest
            file_count += 1
            total_bytes += size

    shasums_path = _shasums_path(snapshot_dir)
    shasum_lines = [f"{digest} {path}" for path, digest in sorted(file_hashes.items())]
    shasums_path.write_text("\n".join(shasum_lines) + ("\n" if shasum_lines else ""), encoding="utf-8")

    bundle_path = _bundle_path(snapshot_dir)
    bundle_sha = _bundle_snapshot(resolved_sources, bundle_path)

    manifest = {
        "snapshot_id": snapshot_id,
        "created_at": _timestamp_iso(now),
        "git_commit": _git_rev(),
        "source": [_rel(path) for path in resolved_sources],
        "files": file_count,
        "bytes": total_bytes,
        "bundle": _rel(bundle_path),
        "manifest": _rel(_manifest_path(snapshot_dir)),
        "shasums": _rel(shasums_path),
        "bundle_sha256": bundle_sha,
        "hashes": dict(sorted(file_hashes.items())),
        "receipts": [],
    }
    if notes:
        manifest["notes"] = notes

    manifest_path = _manifest_path(snapshot_dir)

    receipt_suffix = 0
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = receipt_dir / f"bundle-{stamp_token}.json"
    while receipt_path.exists():
        receipt_suffix += 1
        receipt_path = receipt_dir / f"bundle-{stamp_token}-{receipt_suffix}.json"

    receipt_payload = {
        "snapshot_id": snapshot_id,
        "created_at": manifest["created_at"],
        "bundle": manifest["bundle"],
        "manifest": manifest["manifest"],
        "bundle_sha256": bundle_sha,
        "source": manifest["source"],
        "files": file_count,
        "bytes": total_bytes,
        "shasums": manifest["shasums"],
    }
    if notes:
        receipt_payload["notes"] = notes
    _write_json(receipt_path, receipt_payload)

    manifest["receipts"] = [_rel(receipt_path)]
    _write_json(manifest_path, manifest)

    pointer_payload = {
        "snapshot_id": snapshot_id,
        "created_at": manifest["created_at"],
        "bundle": manifest["bundle"],
        "manifest": manifest["manifest"],
        "receipt": _rel(receipt_path),
        "bundle_sha256": bundle_sha,
    }
    _write_json(receipt_dir / "latest.json", pointer_payload)
    history_path = receipt_dir / "history.jsonl"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(pointer_payload, ensure_ascii=False))
        handle.write("\n")

    if not keep_source:
        for source in resolved_sources:
            shutil.rmtree(source)

    return SnapshotResult(
        snapshot_id=snapshot_id,
        manifest_path=manifest_path,
        bundle_path=bundle_path,
        receipt_path=receipt_path,
        pointer_path=receipt_dir / "latest.json",
    )


def _hash_blob(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def restore(
    *,
    bundle: Path,
    dest: Path,
    manifest: Path | None = None,
    force: bool = False,
) -> Path:
    bundle_path = _ensure_repo_path(_abs(bundle))
    manifest_path = _ensure_repo_path(_abs(manifest)) if manifest else bundle_path.with_name(DEFAULT_MANIFEST_NAME)
    dest_path = _ensure_repo_path(_abs(dest))
    dest_path.mkdir(parents=True, exist_ok=True)
    if any(dest_path.iterdir()) and not force:
        raise ColdStorageError(f"destination not empty: {_rel(dest_path)}")

    if not manifest_path.exists():
        raise ColdStorageError(f"manifest missing: {_rel(manifest_path)}")
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_hash = manifest_data.get("bundle_sha256")
    if not bundle_path.exists():
        raise ColdStorageError(f"bundle missing: {_rel(bundle_path)}")
    actual = _hash_blob(bundle_path)
    if isinstance(expected_hash, str) and actual != expected_hash:
        raise ColdStorageError("bundle hash mismatch")

    decompressor = zstandard.ZstdDecompressor()
    with bundle_path.open("rb") as raw_handle:
        with decompressor.stream_reader(raw_handle) as stream:
            with tarfile.open(fileobj=stream, mode="r|") as archive:
                archive.extractall(dest_path)

    mismatches: list[str] = []
    for rel_path, expected in (manifest_data.get("hashes") or {}).items():
        restored = dest_path / rel_path
        if not restored.exists():
            mismatches.append(f"missing file: {rel_path}")
            continue
        actual_hash, _ = _hash_file(restored)
        if actual_hash != expected:
            mismatches.append(f"hash mismatch: {rel_path}")

    if mismatches:
        raise ColdStorageError("restore completed with mismatches:\n" + "\n".join(mismatches))

    return dest_path


def _parse_timestamp(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def guard(
    *,
    sources: Sequence[Path] | None = None,
    receipt_dir: Path | None = None,
    pointer_path: Path | None = None,
    max_raw: int = 0,
    max_age_days: int = 7,
) -> int:
    resolved_sources = [_ensure_repo_path(_abs(path)) for path in (sources or DEFAULT_RAW_DIRS)]
    receipt_dir = _ensure_repo_path(_abs(receipt_dir or DEFAULT_RECEIPT_DIR))
    pointer_default = receipt_dir / "latest.json"
    pointer = _ensure_repo_path(_abs(pointer_path or pointer_default))

    errors: list[str] = []

    for source in resolved_sources:
        if not source.exists():
            continue
        raw_dirs = [entry for entry in source.iterdir() if entry.is_dir()]
        if max_raw >= 0 and len(raw_dirs) > max_raw:
            errors.append(f"{_rel(source)} contains {len(raw_dirs)} raw directories (max {max_raw})")

    if not pointer.exists():
        errors.append(f"latest pointer missing: {_rel(pointer)}")
    else:
        pointer_data = json.loads(pointer.read_text(encoding="utf-8"))
        manifest = pointer_data.get("manifest")
        bundle = pointer_data.get("bundle")
        receipt = pointer_data.get("receipt")
        created_at = pointer_data.get("created_at")

        if not manifest or not bundle:
            errors.append("pointer missing manifest/bundle references")
        else:
            manifest_path = _ensure_repo_path(_abs(manifest))
            bundle_path = _ensure_repo_path(_abs(bundle))
            if not manifest_path.exists():
                errors.append(f"manifest missing: {_rel(manifest_path)}")
            if not bundle_path.exists():
                errors.append(f"bundle missing: {_rel(bundle_path)}")
            if manifest_path.exists() and bundle_path.exists():
                manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                expected = manifest_data.get("bundle_sha256")
                if expected:
                    actual = _hash_blob(bundle_path)
                    if actual != expected:
                        errors.append("bundle hash mismatch")
                if receipt:
                    receipt_path = _ensure_repo_path(_abs(receipt))
                    if not receipt_path.exists():
                        errors.append(f"receipt missing: {_rel(receipt_path)}")

        parsed = _parse_timestamp(created_at)
        if parsed and max_age_days >= 0:
            age = (_utc_now() - parsed).total_seconds() / 86400
            if age > max_age_days:
                errors.append(
                    f"latest snapshot older than {max_age_days} days (created {created_at})"
                )

    if errors:
        for message in errors:
            print(f"::error:: {message}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot_cmd = subparsers.add_parser("snapshot", help="Archive legacy artifacts into hashed bundles")
    snapshot_cmd.add_argument("--source", action="append", required=True, help="Source directory (repeatable)")
    snapshot_cmd.add_argument("--out", help="Output root (default: artifacts/legacy_cold_storage)")
    snapshot_cmd.add_argument("--receipt", help="Receipt directory (default: _report/usage/legacy-cold-storage)")
    snapshot_cmd.add_argument("--notes", help="Optional notes stored in manifest/receipt")
    snapshot_cmd.add_argument("--keep-source", action="store_true", help="Preserve source directories")
    snapshot_cmd.set_defaults(func=_cmd_snapshot)

    restore_cmd = subparsers.add_parser("restore", help="Restore bundle contents under --dest")
    restore_cmd.add_argument("--bundle", required=True, help="Path to bundle.tar.zst")
    restore_cmd.add_argument("--dest", required=True, help="Destination directory")
    restore_cmd.add_argument("--manifest", help="Override manifest path")
    restore_cmd.add_argument("--force", action="store_true", help="Allow restore into non-empty directory")
    restore_cmd.set_defaults(func=_cmd_restore)

    guard_cmd = subparsers.add_parser("guard", help="Verify pointer freshness and raw artifact hygiene")
    guard_cmd.add_argument("--source", action="append", help="Raw artifact directory to inspect (repeatable)")
    guard_cmd.add_argument("--receipt", help="Receipt directory hosting latest.json")
    guard_cmd.add_argument("--pointer", help="Override pointer path (default: latest.json inside receipt dir)")
    guard_cmd.add_argument(
        "--max-raw",
        type=int,
        default=int(os.getenv("LEGACY_COLD_STORAGE_MAX_RAW", "0")),
        help="Maximum allowed raw directories per source",
    )
    guard_cmd.add_argument(
        "--max-age-days",
        type=int,
        default=int(os.getenv("LEGACY_COLD_STORAGE_MAX_AGE_DAYS", "7")),
        help="Maximum allowed age (days) for latest snapshot",
    )
    guard_cmd.set_defaults(func=_cmd_guard)

    return parser


def _cmd_snapshot(args: argparse.Namespace) -> int:
    try:
        snapshot(
            sources=[Path(item) for item in args.source],
            out_dir=Path(args.out) if args.out else None,
            receipt_dir=Path(args.receipt) if args.receipt else None,
            keep_source=bool(getattr(args, "keep_source", False)),
            notes=getattr(args, "notes", None),
        )
    except ColdStorageError as exc:
        print(f"cold_storage snapshot: {exc}")
        return 1
    return 0


def _cmd_restore(args: argparse.Namespace) -> int:
    try:
        restore(
            bundle=Path(args.bundle),
            dest=Path(args.dest),
            manifest=Path(args.manifest) if args.manifest else None,
            force=bool(getattr(args, "force", False)),
        )
    except ColdStorageError as exc:
        print(f"cold_storage restore: {exc}")
        return 1
    return 0


def _cmd_guard(args: argparse.Namespace) -> int:
    sources = [Path(item) for item in args.source] if args.source else None
    receipt_dir = Path(args.receipt) if args.receipt else None
    pointer = Path(args.pointer) if args.pointer else None
    return guard(
        sources=sources,
        receipt_dir=receipt_dir,
        pointer_path=pointer,
        max_raw=args.max_raw,
        max_age_days=args.max_age_days,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    func = getattr(args, "func", None)
    if not callable(func):
        parser.print_help()
        return 2
    return func(args)


if __name__ == "__main__":
    raise SystemExit(main())
