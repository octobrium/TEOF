from __future__ import annotations

import json
from pathlib import Path

import teof.bootloader as bootloader


def _write_manifest(root: Path, entries: list[dict[str, object]]) -> Path:
    receipts_dir = root / "receipts"
    receipts_dir.mkdir(parents=True, exist_ok=True)
    receipts_path = receipts_dir / "index.jsonl"
    receipts_path.write_text("\n".join(json.dumps(entry) for entry in entries) + "\n", encoding="utf-8")
    manifest = root / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "paths": {
                    "receipts": ["receipts/index.jsonl"],
                }
            }
        ),
        encoding="utf-8",
    )
    return manifest


def test_teof_receipts_stream_cli(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path,
        [
            {"path": "_report/a.json", "mtime": "2025-11-09T07:00:00Z", "sha256": "1"},
            {"path": "_report/b.json", "mtime": "2025-11-09T07:01:00Z", "sha256": "2"},
            {"path": "_report/c.json", "mtime": "2025-11-09T07:02:00Z", "sha256": "3"},
        ],
    )
    dest = tmp_path / "stream"
    pointer = tmp_path / "latest.json"
    receipt = tmp_path / "receipt.json"

    exit_code = bootloader.main(
        [
            "receipts_stream",
            "--manifest",
            str(manifest),
            "--dest",
            str(dest),
            "--pointer",
            str(pointer),
            "--max-entries",
            "2",
            "--receipt",
            str(receipt),
            "--max-age-hours",
            "0",
        ]
    )
    assert exit_code == 0

    shard_files = sorted(dest.glob("receipts-*.jsonl"))
    assert len(shard_files) == 2
    pointer_payload = json.loads(pointer.read_text(encoding="utf-8"))
    assert pointer_payload["latest"].endswith(".jsonl")
    assert pointer_payload["sequence"] == 2
    receipt_payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert receipt_payload["module"] == "tools.autonomy.receipts_index_stream"
    assert receipt_payload["command"] == "teof receipts_stream"
    assert receipt_payload["pointer"]["path"] == pointer.as_posix()
    assert receipt_payload["stats"]["shards_created"] == 2
    assert receipt_payload["stats"]["new_entries"] == 3
