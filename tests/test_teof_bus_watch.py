from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import teof.bootloader as bootloader
from tools.agent import bus_watch


def _setup_events(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[str, str]:
    events_log = tmp_path / "events.jsonl"
    events_log.parent.mkdir(parents=True, exist_ok=True)

    now = datetime(2025, 9, 18, 1, 0, tzinfo=timezone.utc)

    def iso(minutes: int) -> str:
        return (now + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")

    entries = [
        {
            "ts": iso(0),
            "agent_id": "codex-1",
            "event": "status",
            "summary": "fresh heartbeat",
            "task_id": "QUEUE-010",
        },
        {
            "ts": iso(-60),
            "agent_id": "codex-2",
            "event": "note",
            "summary": "older note",
            "task_id": "manager-report",
        },
    ]
    with events_log.open("w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry) + "\n")

    monkeypatch.setattr(bus_watch, "EVENT_LOG", events_log)
    monkeypatch.setattr(bus_watch, "utc_now", lambda: now)
    return iso(0), iso(-30)


def test_teof_bus_watch_filters_by_agent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup_events(tmp_path, monkeypatch)

    exit_code = bootloader.main(["bus_watch", "--agent", "codex-1", "--window-hours", "0", "--limit", "5"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "codex-1" in out
    assert "fresh heartbeat" in out
    assert "codex-2" not in out


def test_teof_bus_watch_since_filter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    latest_ts, since_ts = _setup_events(tmp_path, monkeypatch)

    exit_code = bootloader.main(["bus_watch", "--since", since_ts, "--window-hours", "0"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert latest_ts in out
    assert "older note" not in out
