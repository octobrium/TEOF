from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from scripts.ci import check_receipts_stream as guard


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _make_shard(repo: Path, contents: str) -> tuple[Path, str]:
    shard_path = repo / "_report" / "usage" / "receipts-index" / "stream" / "receipts-test.jsonl"
    shard_path.parent.mkdir(parents=True, exist_ok=True)
    shard_path.write_text(contents, encoding="utf-8")
    sha = hashlib.sha256(shard_path.read_bytes()).hexdigest()
    return shard_path, sha


def test_receipts_stream_guard_happy_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    monkeypatch.setattr(guard, "ROOT", repo)
    monkeypatch.setattr(guard.guard, "ROOT", repo)
    monkeypatch.delenv("RECEIPTS_STREAM_MAX_AGE_HOURS", raising=False)

    shard_path, sha = _make_shard(repo, "{}\n")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest_path = shard_path.with_suffix(".manifest.json")
    _write_json(
        manifest_path,
        {
            "shard_id": "receipts-test",
            "sequence": 1,
            "last_timestamp": now,
            "sha256": sha,
        },
    )
    pointer_path = repo / "_report" / "usage" / "receipts-index" / "latest.json"
    _write_json(
        pointer_path,
        {
            "latest": "_report/usage/receipts-index/stream/receipts-test.jsonl",
            "sha256": sha,
            "sequence": 1,
            "generated_at": now,
        },
    )

    assert guard.main() == 0


def test_receipts_stream_guard_fails_when_stale(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    repo = tmp_path / "repo"
    monkeypatch.setattr(guard, "ROOT", repo)
    monkeypatch.setattr(guard.guard, "ROOT", repo)
    monkeypatch.setenv("RECEIPTS_STREAM_MAX_AGE_HOURS", "0.001")

    shard_path, sha = _make_shard(repo, "{}\n")
    old_ts = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest_path = shard_path.with_suffix(".manifest.json")
    _write_json(
        manifest_path,
        {
            "shard_id": "receipts-test",
            "sequence": 1,
            "last_timestamp": old_ts,
            "sha256": sha,
        },
    )
    pointer_path = repo / "_report" / "usage" / "receipts-index" / "latest.json"
    _write_json(
        pointer_path,
        {
            "latest": "_report/usage/receipts-index/stream/receipts-test.jsonl",
            "sha256": sha,
            "sequence": 1,
            "generated_at": old_ts,
        },
    )

    assert guard.main() == 1
    err = capsys.readouterr().err
    assert "stale" in err
