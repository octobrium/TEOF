import json
from pathlib import Path

from tools.usage import logger


def test_record_usage_creates_log(monkeypatch, tmp_path):
    log = tmp_path / "usage" / "tools.jsonl"
    monkeypatch.setattr(logger, "USAGE_DIR", tmp_path / "usage")
    monkeypatch.setattr(logger, "USAGE_LOG", log)
    monkeypatch.setattr(logger, "_now_iso", lambda: "2025-09-18T00:00:00Z")

    logger.record_usage("task_sync", action="dry-run", extra={"changes": 2})
    logger.record_usage("task_sync")

    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2

    first = json.loads(lines[0])
    assert first == {
        "tool": "task_sync",
        "action": "dry-run",
        "ts": "2025-09-18T00:00:00Z",
        "changes": 2,
    }
