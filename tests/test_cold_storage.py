from __future__ import annotations

import json
import shutil
from pathlib import Path

from tools.artifacts import cold_storage


def _workspace(tmp_path: Path) -> Path:
    root = cold_storage.ROOT / "tests" / "tmp" / tmp_path.name
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_snapshot_restore_and_guard(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    try:
        legacy_report = workspace / "_report" / "legacy_loop_out" / "run-1"
        legacy_report.mkdir(parents=True, exist_ok=True)
        (legacy_report / "summary.txt").write_text("alpha", encoding="utf-8")
        apoptosis_dir = workspace / "_apoptosis" / "run-2"
        apoptosis_dir.mkdir(parents=True, exist_ok=True)
        (apoptosis_dir / "notes.txt").write_text("beta", encoding="utf-8")

        out_dir = workspace / "artifacts" / "legacy_cold_storage"
        receipt_dir = workspace / "_report" / "usage" / "legacy-cold-storage"

        rc = cold_storage.main(
            [
                "snapshot",
                "--source",
                str(legacy_report),
                "--source",
                str(apoptosis_dir),
                "--out",
                str(out_dir),
                "--receipt",
                str(receipt_dir),
                "--notes",
                "test snapshot",
            ]
        )
        assert rc == 0

        bundles = list(out_dir.glob("legacy-*"))
        assert len(bundles) == 1
        bundle_dir = bundles[0]
        bundle = bundle_dir / "bundle.tar.zst"
        manifest_path = bundle_dir / "manifest.json"
        shasums_path = bundle_dir / "SHASUMS.txt"
        assert bundle.exists()
        assert manifest_path.exists()
        assert shasums_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["files"] == 2
        assert manifest["receipts"]
        receipt_path = receipt_dir / Path(manifest["receipts"][0]).name
        assert receipt_path.exists()
        pointer_path = receipt_dir / "latest.json"
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        assert pointer["bundle"].endswith("bundle.tar.zst")

        restore_dir = workspace / "restore"
        rc = cold_storage.main(
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
        restored_files = sorted(p.relative_to(restore_dir).as_posix() for p in restore_dir.rglob("*.txt"))
        prefix = workspace.relative_to(cold_storage.ROOT).as_posix()
        assert restored_files == [
            f"{prefix}/_apoptosis/run-2/notes.txt",
            f"{prefix}/_report/legacy_loop_out/run-1/summary.txt",
        ]

        rc = cold_storage.main(
            [
                "guard",
                "--source",
                str(workspace / "_report" / "legacy_loop_out"),
                "--source",
                str(workspace / "_apoptosis"),
                "--receipt",
                str(receipt_dir),
                "--max-raw",
                "0",
                "--max-age-days",
                "30",
            ]
        )
        assert rc == 0
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def test_guard_detects_raw_directories_when_not_cleaned(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    try:
        legacy_report = workspace / "_report" / "legacy_loop_out" / "run-raw"
        legacy_report.mkdir(parents=True, exist_ok=True)
        (legacy_report / "summary.txt").write_text("alpha", encoding="utf-8")
        out_dir = workspace / "artifacts" / "legacy_cold_storage"
        receipt_dir = workspace / "_report" / "usage" / "legacy-cold-storage"

        rc = cold_storage.main(
            [
                "snapshot",
                "--source",
                str(legacy_report),
                "--out",
                str(out_dir),
                "--receipt",
                str(receipt_dir),
                "--keep-source",
            ]
        )
        assert rc == 0

        rc = cold_storage.main(
            [
                "guard",
                "--source",
                str(workspace / "_report" / "legacy_loop_out"),
                "--receipt",
                str(receipt_dir),
                "--max-raw",
                "0",
                "--max-age-days",
                "30",
            ]
        )
        assert rc == 1
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
