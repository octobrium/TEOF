from __future__ import annotations

import json
from pathlib import Path

from tools.autonomy import apoptosis_compress


def _create_snapshot(root: Path) -> Path:
    snapshot = root / "snapshot"
    snapshot.mkdir()
    (snapshot / "a.txt").write_text("hello", encoding="utf-8")
    nested = snapshot / "nested"
    nested.mkdir()
    (nested / "b.txt").write_text("world", encoding="utf-8")
    return snapshot


def test_bundle_and_restore(tmp_path: Path) -> None:
    source = _create_snapshot(tmp_path)
    artifacts = tmp_path / "artifacts"
    receipts = tmp_path / "receipts"

    rc = apoptosis_compress.main(
        [
            "bundle",
            str(source),
            "--out-dir",
            str(artifacts),
            "--receipt-dir",
            str(receipts),
            "--keep-source",
        ]
    )
    assert rc == 0

    bundle_dirs = list(artifacts.iterdir())
    assert bundle_dirs, "bundle directory not created"
    bundle_dir = bundle_dirs[0]
    bundle = bundle_dir / "bundle.tar.xz"
    manifest_path = bundle_dir / "manifest.json"
    assert bundle.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["file_count"] == 2
    assert manifest["receipts"]

    latest_receipt = receipts / "latest.json"
    assert latest_receipt.exists()

    restore_dir = tmp_path / "restore"
    rc = apoptosis_compress.main(
        [
            "restore",
            "--bundle",
            str(bundle),
            "--manifest",
            str(manifest_path),
            "--dest",
            str(restore_dir),
            "--force",
        ]
    )
    assert rc == 0
    restored_files = sorted(p.relative_to(restore_dir) for p in restore_dir.rglob("*.txt"))
    assert restored_files


def test_verify_passes(tmp_path: Path) -> None:
    source = _create_snapshot(tmp_path)
    artifacts = tmp_path / "artifacts"
    receipts = tmp_path / "receipts"
    apoptosis_compress.main(
        [
            "bundle",
            str(source),
            "--out-dir",
            str(artifacts),
            "--receipt-dir",
            str(receipts),
        ]
    )
    bundle_dir = next(iter(artifacts.iterdir()))
    rc = apoptosis_compress.main(
        [
            "verify",
            "--manifest",
            str(bundle_dir / "manifest.json"),
        ]
    )
    assert rc == 0
