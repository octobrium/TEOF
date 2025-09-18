from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.agent import session_brief


def _write_jsonl(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + "\n")


def test_session_brief_outputs_claim_and_logs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(session_brief, "CLAIMS_DIR", tmp_path / "claims")
    monkeypatch.setattr(session_brief, "EVENT_LOG", tmp_path / "events.jsonl")
    monkeypatch.setattr(session_brief, "MESSAGES_DIR", tmp_path / "messages")

    claim_path = session_brief.CLAIMS_DIR / "QUEUE-150.json"
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    claim_path.write_text(
        json.dumps(
            {
                "agent_id": "codex-4",
                "task_id": "QUEUE-150",
                "status": "paused",
                "plan_id": "2025-plan",
                "branch": "agent/codex-4/queue-150",
                "claimed_at": "2025-09-18T20:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    _write_jsonl(
        session_brief.EVENT_LOG,
        [
            {
                "ts": "2025-09-18T20:05:00Z",
                "agent_id": "codex-4",
                "event": "status",
                "task_id": "QUEUE-150",
                "summary": "Working on helper",
            },
            {
                "ts": "2025-09-18T20:10:00Z",
                "agent_id": "codex-4",
                "event": "complete",
                "task_id": "QUEUE-150",
                "summary": "Helper done",
            },
        ],
    )

    task_messages = session_brief.MESSAGES_DIR / "QUEUE-150.jsonl"
    _write_jsonl(
        task_messages,
        [
            {
                "ts": "2025-09-18T20:06:00Z",
                "from": "codex-1",
                "type": "status",
                "task_id": "QUEUE-150",
                "summary": "Manager review scheduled",
            }
        ],
    )

    exit_code = session_brief.main(["--task", "QUEUE-150", "--limit", "2"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Task: QUEUE-150" in out
    assert "Agent: codex-4" in out
    assert "Events" in out and "complete" in out
    assert "Messages" in out and "Manager review scheduled" in out


def test_session_brief_without_claim(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(session_brief, "CLAIMS_DIR", tmp_path / "claims")
    monkeypatch.setattr(session_brief, "EVENT_LOG", tmp_path / "events.jsonl")
    monkeypatch.setattr(session_brief, "MESSAGES_DIR", tmp_path / "messages")

    exit_code = session_brief.main(["--task", "QUEUE-151"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "No claim found" in out
