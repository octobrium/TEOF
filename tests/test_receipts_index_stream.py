from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.autonomy import receipts_index_stream as ris


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_manifest(repo: Path, receipts: list[str]) -> Path:
    manifest = {
        "paths": {
            "receipts": receipts,
        }
    }
    manifest_path = repo / "_report" / "usage" / "receipts-index" / "manifest.json"
    _write(manifest_path, json.dumps(manifest))
    return manifest_path


def test_stream_emits_shards_and_pointer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    monkeypatch.setattr(ris, "ROOT", repo)
    receipts_dir = repo / "_report" / "usage" / "receipts-index" / "receipts"
    receipts_file = receipts_dir / "receipts-0001.jsonl"
    now = "2025-11-09T06:30:00Z"
    entries = [
        {"kind": "receipt", "path": "_report/a.json", "mtime": now, "sha256": "1"},
        {"kind": "receipt", "path": "_report/b.json", "mtime": now, "sha256": "2"},
        {"kind": "receipt", "path": "_report/c.json", "mtime": now, "sha256": "3"},
    ]
    _write(receipts_file, "\n".join(json.dumps(entry) for entry in entries) + "\n")
    manifest_path = _make_manifest(repo, ["receipts/receipts-0001.jsonl"])

    dest = repo / "_report" / "usage" / "receipts-index" / "stream"
    pointer = repo / "_report" / "usage" / "receipts-index" / "latest.json"

    receipt_path = repo / "_report" / "usage" / "receipts-index" / "stream-run.json"
    rc = ris.main(
        [
            "stream",
            "--manifest",
            str(manifest_path),
            "--dest",
            str(dest),
            "--pointer",
            str(pointer),
            "--max-entries",
            "2",
            "--max-age-hours",
            "0",
            "--receipt",
            str(receipt_path),
        ]
    )
    assert rc == 0
    shard_files = sorted(dest.glob("receipts-*.jsonl"))
    assert len(shard_files) == 2
    manifest_files = sorted(dest.glob("receipts-*.manifest.json"))
    assert len(manifest_files) == 2
    pointer_payload = json.loads(pointer.read_text(encoding="utf-8"))
    assert pointer_payload["latest"].startswith("_report/usage/receipts-index/stream/receipts-")
    assert pointer_payload["sequence"] >= 1
    receipt_payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt_payload["module"] == "tools.autonomy.receipts_index_stream"
    assert receipt_payload["stats"]["shards_created"] == 2
    assert receipt_payload["pointer"]["path"].endswith("receipts-index/latest.json")


def test_stream_staleness_guard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    monkeypatch.setattr(ris, "ROOT", repo)
    receipts_dir = repo / "_report" / "usage" / "receipts-index" / "receipts"
    receipts_file = receipts_dir / "receipts-0001.jsonl"
    old_ts = "2020-01-01T00:00:00Z"
    _write(
        receipts_file,
        json.dumps({"kind": "receipt", "path": "_report/a.json", "mtime": old_ts, "sha256": "1"}) + "\n",
    )
    manifest_path = _make_manifest(repo, ["receipts/receipts-0001.jsonl"])
    dest = repo / "_report" / "usage" / "receipts-index" / "stream"
    pointer = repo / "_report" / "usage" / "receipts-index" / "latest.json"

    # First run creates the shard.
    assert (
        ris.main(
            [
                "stream",
                "--manifest",
                str(manifest_path),
                "--dest",
                str(dest),
                "--pointer",
                str(pointer),
                "--max-age-hours",
                "1000000",
            ]
        )
        == 0
    )

    # Second run sees no new entries, but the last shard is stale → guard fails.
    with pytest.raises(SystemExit):
        ris.main(
            [
                "stream",
                "--manifest",
                str(manifest_path),
                "--dest",
                str(dest),
                "--pointer",
                str(pointer),
                "--max-age-hours",
                "0.0001",
            ]
        )
