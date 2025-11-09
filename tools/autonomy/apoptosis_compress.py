"""Bundle apoptosis snapshots into hashed archives with restore/verify helpers."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tarfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from tools.autonomy.shared import atomic_write_json, atomic_write_text, utc_timestamp

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_ROOT = ROOT / "_apoptosis"
DEFAULT_BUNDLE_ROOT = ROOT / "artifacts" / "apoptosis"
DEFAULT_RECEIPT_ROOT = ROOT / "_report" / "usage" / "apoptosis"


@dataclass
class BundleMeta:
    bundle_id: str
    source_dir: Path
    bundle_dir: Path
    bundle_path: Path
    manifest_path: Path
    shasums_path: Path
    receipt_dir: Path


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _default_bundle_id(source: Path) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{source.name}-{stamp}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _scan_files(source: Path) -> list[Path]:
    return [path for path in source.rglob("*") if path.is_file()]


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_receipt(meta: BundleMeta, manifest: dict) -> Path:
    _ensure_dir(meta.receipt_dir)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    receipt_path = meta.receipt_dir / f"bundle-{timestamp}.json"
    payload = {
        "bundle_id": manifest["bundle_id"],
        "created_at": manifest["created_at"],
        "source_dir": manifest["source_dir"],
        "bundle_path": manifest["bundle_path"],
        "manifest_path": manifest["manifest_path"],
        "bundle_sha256": manifest["bundle_sha256"],
        "file_count": manifest["file_count"],
        "total_bytes": manifest["total_bytes"],
        "notes": manifest.get("notes"),
    }
    atomic_write_json(receipt_path, payload)
    latest = meta.receipt_dir / "latest.json"
    atomic_write_json(latest, {"latest": _rel(receipt_path)})
    return receipt_path


def cmd_bundle(args: argparse.Namespace) -> int:
    source = Path(args.source)
    if not source.is_absolute():
        source = ROOT / source
    if not source.exists():
        raise SystemExit(f"source directory missing: {source}")
    bundle_id = args.bundle_id or _default_bundle_id(source)
    bundle_root = Path(args.out_dir) if args.out_dir else DEFAULT_BUNDLE_ROOT
    if not bundle_root.is_absolute():
        bundle_root = ROOT / bundle_root
    bundle_dir = bundle_root / bundle_id
    bundle_dir.mkdir(parents=True, exist_ok=True)

    bundle_path = bundle_dir / "bundle.tar.xz"
    manifest_path = bundle_dir / "manifest.json"
    shasums_path = bundle_dir / "SHASUMS.txt"
    receipt_dir = Path(args.receipt_dir) if args.receipt_dir else DEFAULT_RECEIPT_ROOT
    if not receipt_dir.is_absolute():
        receipt_dir = ROOT / receipt_dir

    files = _scan_files(source)
    if not files:
        raise SystemExit(f"source directory empty: {source}")

    file_hashes: dict[str, str] = {}
    total_bytes = 0
    with shasums_path.open("w", encoding="utf-8") as shasums:
        for file in files:
            rel = file.relative_to(source)
            digest = _sha256(file)
            file_hashes[rel.as_posix()] = digest
            shasums.write(f"{digest}  {rel.as_posix()}\n")
            total_bytes += file.stat().st_size

    with tarfile.open(bundle_path, "w:xz") as tar:
        tar.add(source, arcname=source.name)

    bundle_sha = _sha256(bundle_path)
    manifest = {
        "bundle_id": bundle_id,
        "created_at": utc_timestamp(),
        "source_dir": _rel(source),
        "bundle_path": _rel(bundle_path),
        "manifest_path": _rel(manifest_path),
        "file_count": len(files),
        "total_bytes": total_bytes,
        "bundle_sha256": bundle_sha,
        "hashes": file_hashes,
        "notes": args.notes,
    }

    receipt_path = _write_receipt(
        BundleMeta(
            bundle_id,
            source,
            bundle_dir,
            bundle_path,
            manifest_path,
            shasums_path,
            receipt_dir,
        ),
        manifest,
    )
    manifest["receipts"] = [_rel(receipt_path)]
    atomic_write_json(manifest_path, manifest)

    if not args.keep_source:
        shutil.rmtree(source)

    print(f"bundle created → {bundle_path.relative_to(ROOT) if bundle_path.is_relative_to(ROOT) else bundle_path}")
    print(f"manifest → {manifest_path.relative_to(ROOT) if manifest_path.is_relative_to(ROOT) else manifest_path}")
    print(f"receipt → {_rel(receipt_path)}")
    return 0


def _load_manifest(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"manifest missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid manifest JSON: {exc}")


def cmd_restore(args: argparse.Namespace) -> int:
    bundle = Path(args.bundle)
    if not bundle.is_absolute():
        bundle = ROOT / bundle
    if not bundle.exists():
        raise SystemExit(f"bundle missing: {bundle}")
    manifest_path = Path(args.manifest) if args.manifest else bundle.parent / "manifest.json"
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    manifest = _load_manifest(manifest_path)
    expected_sha = manifest.get("bundle_sha256")
    if expected_sha:
        actual_sha = _sha256(bundle)
        if actual_sha != expected_sha:
            raise SystemExit(f"bundle hash mismatch (expected {expected_sha}, got {actual_sha})")
    dest = Path(args.dest)
    if not dest.is_absolute():
        dest = ROOT / dest
    if dest.exists() and not args.force:
        raise SystemExit(f"destination exists: {dest} (use --force to overwrite)")
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(bundle, "r:*") as tar:
        tar.extractall(dest)
    print(f"restored bundle into {dest}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    manifest = _load_manifest(manifest_path)
    bundle_path = Path(args.bundle) if args.bundle else manifest_path.parent / "bundle.tar.xz"
    if not bundle_path.is_absolute():
        bundle_path = ROOT / bundle_path
    actual_sha = _sha256(bundle_path)
    expected_sha = manifest.get("bundle_sha256")
    if expected_sha != actual_sha:
        raise SystemExit(f"bundle hash mismatch (expected {expected_sha}, got {actual_sha})")
    print("bundle hash verified")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    bundle = sub.add_parser("bundle", help="Bundle a snapshot directory into a compressed archive")
    bundle.add_argument("source", help="Path to the snapshot directory to bundle")
    bundle.add_argument("--bundle-id", help="Custom bundle id (default: <source>-<UTC>)")
    bundle.add_argument("--out-dir", help="Directory to store bundles (default: artifacts/apoptosis)")
    bundle.add_argument("--receipt-dir", help="Directory for bundle receipts (default: _report/usage/apoptosis)")
    bundle.add_argument("--notes", help="Optional notes to embed in manifest/receipt")
    bundle.add_argument("--keep-source", action="store_true", help="Keep the source directory after bundling")
    bundle.set_defaults(func=cmd_bundle)

    restore = sub.add_parser("restore", help="Restore a bundle into a destination directory")
    restore.add_argument("--bundle", required=True, help="Path to bundle.tar.xz")
    restore.add_argument("--dest", required=True, help="Destination directory for extraction")
    restore.add_argument("--manifest", help="Path to manifest.json (default: alongside bundle)")
    restore.add_argument("--force", action="store_true", help="Overwrite destination if it exists")
    restore.set_defaults(func=cmd_restore)

    verify = sub.add_parser("verify", help="Verify a bundle against its manifest")
    verify.add_argument("--manifest", required=True, help="Path to manifest.json")
    verify.add_argument("--bundle", help="Bundle path (default: bundle.tar.xz next to manifest)")
    verify.set_defaults(func=cmd_verify)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
