from __future__ import annotations

import json
from pathlib import Path

import pytest

import teof.bootloader as bootloader
from tools.agent import bus_inbox


def _setup_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    root = tmp_path
    messages_dir = root / "_bus" / "messages"
    session_dir = root / "_report" / "session"
    manifest = root / "AGENT_MANIFEST.json"
    manifest.write_text(json.dumps({"agent_id": "codex-9"}), encoding="utf-8")
    messages_dir.mkdir(parents=True, exist_ok=True)
    session_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(bus_inbox, "ROOT", root)
    monkeypatch.setattr(bus_inbox, "MESSAGES_DIR", messages_dir)
    monkeypatch.setattr(bus_inbox, "SESSION_REPORT_DIR", session_dir)
    monkeypatch.setattr(bus_inbox, "MANIFEST_PATH", manifest)

    return messages_dir, session_dir


def _write_entries(path: Path) -> None:
    entries = [
        {"ts": "2025-11-09T02:00:00Z", "summary": "first ping"},
        {"ts": "2025-11-09T02:05:00Z", "summary": "second ping"},
        {"ts": "2025-11-09T02:06:00Z", "summary": "final ping"},
    ]
    serialized = "\n".join(json.dumps(entry) for entry in entries) + "\n"
    path.write_text(serialized, encoding="utf-8")


def test_teof_inbox_command_captures_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    messages_dir, session_dir = _setup_repo(tmp_path, monkeypatch)
    channel = messages_dir / "agent-codex-9.jsonl"
    _write_entries(channel)

    exit_code = bootloader.main(["inbox", "--agent", "codex-9", "--limit", "2", "--mark-read"])
    assert exit_code == 0

    output = capsys.readouterr().out
    assert "Inbox agent-codex-9" in output
    tail_path = session_dir / "codex-9" / "agent-inbox-tail.txt"
    assert tail_path.exists()
    state_path = session_dir / "codex-9" / "agent-inbox-state.json"
    assert state_path.exists()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["last_seen_ts"] == "2025-11-09T02:06:00Z"
