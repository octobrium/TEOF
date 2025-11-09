import json
from pathlib import Path

import pytest

from tools.agent import bus_inbox


def _setup_env(monkeypatch, tmp_path: Path, agent_id: str = "codex-9"):
    root = tmp_path
    manifest = root / "AGENT_MANIFEST.json"
    manifest.write_text(json.dumps({"agent_id": agent_id}), encoding="utf-8")
    messages_dir = root / "_bus" / "messages"
    session_dir = root / "_report" / "session"
    messages_dir.mkdir(parents=True, exist_ok=True)
    session_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(bus_inbox, "ROOT", root)
    monkeypatch.setattr(bus_inbox, "MESSAGES_DIR", messages_dir)
    monkeypatch.setattr(bus_inbox, "SESSION_REPORT_DIR", session_dir)
    monkeypatch.setattr(bus_inbox, "MANIFEST_PATH", manifest)

    return messages_dir, session_dir, agent_id


def _write_inbox(messages_dir: Path, agent_id: str, entries: list[dict[str, object]]) -> Path:
    path = messages_dir / f"agent-{agent_id}.jsonl"
    serialized = "\n".join(json.dumps(item) for item in entries) + "\n"
    path.write_text(serialized, encoding="utf-8")
    return path


def test_inspect_inbox_marks_state_and_receipt(monkeypatch, tmp_path):
    messages_dir, session_dir, agent = _setup_env(monkeypatch, tmp_path)
    entries = [
        {"ts": "2025-11-09T01:00:00Z", "summary": "ping-1"},
        {"ts": "2025-11-09T01:01:00Z", "summary": "ping-2"},
        {"ts": "2025-11-09T01:02:00Z", "summary": "ping-3"},
    ]
    _write_inbox(messages_dir, agent, entries)

    summary = bus_inbox.inspect_inbox(agent_id=agent, limit=2, mark_read=True)

    assert summary.total_messages == 3
    assert summary.new_messages == 3
    assert summary.receipt_path is not None
    assert summary.receipt_path.exists()
    state_content = json.loads(summary.state_path.read_text(encoding="utf-8"))
    assert state_content["last_seen_ts"] == "2025-11-09T01:02:00Z"
    receipt_text = summary.receipt_path.read_text(encoding="utf-8")
    assert "written_entries=2" in receipt_text
    assert "unread_since_state=3" in receipt_text


def test_inspect_inbox_counts_new_since_existing_state(monkeypatch, tmp_path):
    messages_dir, session_dir, agent = _setup_env(monkeypatch, tmp_path)
    entries = [
        {"ts": "2025-11-09T01:10:00Z", "summary": "hello"},
        {"ts": "2025-11-09T01:11:00Z", "summary": "world"},
        {"ts": "2025-11-09T01:12:00Z", "summary": "again"},
    ]
    _write_inbox(messages_dir, agent, entries)
    state_path = session_dir / agent / "agent-inbox-state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"last_seen_ts": "2025-11-09T01:11:00Z"}), encoding="utf-8")

    summary = bus_inbox.inspect_inbox(
        agent_id=agent,
        limit=5,
        capture_receipt=False,
    )

    assert summary.new_messages == 1
    assert summary.total_messages == 3
    assert summary.receipt_path is None


def test_bus_inbox_cli_handles_missing_channel(monkeypatch, tmp_path, capsys):
    _setup_env(monkeypatch, tmp_path, agent_id="codex-8")

    exit_code = bus_inbox.main(["--agent", "codex-8", "--limit", "3"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "total=0" in out
    assert "agent-codex-8" in out
