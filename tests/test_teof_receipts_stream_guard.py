from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import teof.bootloader as bootloader


def _write_shard_bundle(root: Path, *, age_days: int) -> Path:
    shard = root / "receipts-0001.jsonl"
    shard.write_text("{}\n", encoding="utf-8")
    digest = hashlib.sha256(shard.read_bytes()).hexdigest()
    timestamp = datetime.now(timezone.utc) - timedelta(days=age_days)
    ts_str = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest = shard.with_suffix(".manifest.json")
    manifest.write_text(
        json.dumps(
            {
                "shard_id": "receipts-0001",
                "sequence": 1,
                "last_timestamp": ts_str,
                "sha256": digest,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    pointer = root / "latest.json"
    pointer.write_text(
        json.dumps(
            {
                "latest": shard.as_posix(),
                "sha256": digest,
                "sequence": 1,
                "generated_at": ts_str,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return pointer


def test_teof_receipts_stream_guard_success(tmp_path: Path) -> None:
    pointer = _write_shard_bundle(tmp_path, age_days=0)
    receipt = tmp_path / "guard-success.json"
    exit_code = bootloader.main(
        [
            "receipts_stream_guard",
            "--pointer",
            str(pointer),
            "--max-age-hours",
            "24",
            "--receipt",
            str(receipt),
        ]
    )
    assert exit_code == 0
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert payload["module"] == "tools.autonomy.receipts_stream_guard"
    assert payload["status"] == "ok"
    assert payload["pointer"].endswith("latest.json")


def test_teof_receipts_stream_guard_stale(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pointer = _write_shard_bundle(tmp_path, age_days=10)
    receipt = tmp_path / "guard-failure.json"
    exit_code = bootloader.main(
        [
            "receipts_stream_guard",
            "--pointer",
            str(pointer),
            "--max-age-hours",
            "0.001",
            "--receipt",
            str(receipt),
        ]
    )
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "stale" in err
    failure = json.loads(receipt.read_text(encoding="utf-8"))
    assert failure["status"] == "error"
    assert "stale" in failure["message"]
