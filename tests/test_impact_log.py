from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.receipts import log_event


def test_write_entry_appends(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log_path = tmp_path / "memory" / "impact" / "log.jsonl"
    monkeypatch.setattr(log_event, "IMPACT_LOG_PATH", log_path)

    entry = {
        "recorded_at": "2025-09-23T00:00:00Z",
        "title": "Outcome",
        "value": 123.4,
        "currency": "USD",
        "description": "Demo",
        "receipts": ["memory/reflections/reflection-demo.json"],
        "notes": "",
    }

    log_event.write_impact_entry(entry, dry_run=False)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["title"] == "Outcome"
    assert payload["value"] == 123.4


def test_main_dry_run(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    rc = log_event.main(
        [
            "impact",
            "--title",
            "Dry run",
            "--value",
            "0",
            "--description",
            "Preview",
            "--dry-run",
        ]
    )
    assert rc == 0
    output = capsys.readouterr().out
    assert "Dry run" in output
