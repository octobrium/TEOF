import json
from pathlib import Path

import pytest

from tools.agent import bus_message


def test_bus_message_appends_jsonl(tmp_path, monkeypatch, capsys):
    messages_dir = tmp_path / "messages"
    monkeypatch.setattr(bus_message, "MESSAGES_DIR", messages_dir)
    monkeypatch.setattr(bus_message, "MANIFEST_PATH", tmp_path / "manifest.json")
    (tmp_path / "manifest.json").write_text(json.dumps({"agent_id": "codex-2"}), encoding="utf-8")

    exit_code = bus_message.main(
        [
            "--task",
            "QUEUE-005",
            "--type",
            "note",
            "--summary",
            "Testing message",
            "--receipt",
            "_report/test.json",
            "--meta",
            "priority=high",
            "--note",
            "idle availability",
        ]
    )
    assert exit_code == 0

    path = messages_dir / "QUEUE-005.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["from"] == "codex-2"
    assert payload["task_id"] == "QUEUE-005"
    assert payload["receipts"] == ["_report/test.json"]
    assert payload["meta"]["priority"] == "high"
    assert payload["note"] == "idle availability"


def test_bus_message_requires_agent(tmp_path, monkeypatch):
    messages_dir = tmp_path / "messages"
    monkeypatch.setattr(bus_message, "MESSAGES_DIR", messages_dir)
    monkeypatch.setattr(bus_message, "MANIFEST_PATH", tmp_path / "manifest.json")

    with pytest.raises(SystemExit) as exc:
        bus_message.main(
            [
                "--task",
                "QUEUE-005",
                "--type",
                "note",
                "--summary",
                "No agent",
            ]
        )
    assert "agent id required" in str(exc.value)
