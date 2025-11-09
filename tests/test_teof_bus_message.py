import json
from pathlib import Path

import pytest

import teof.bootloader as bootloader
from tools.agent import bus_message


def _setup_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path
    messages_dir = root / "_bus" / "messages"
    claims_dir = root / "_bus" / "claims"
    messages_dir.mkdir(parents=True, exist_ok=True)
    claims_dir.mkdir(parents=True, exist_ok=True)
    manifest = root / "AGENT_MANIFEST.json"
    manifest.write_text(json.dumps({"agent_id": "codex-9"}), encoding="utf-8")
    claim_path = claims_dir / "QUEUE-300.json"
    claim_path.write_text(
        json.dumps({"task_id": "QUEUE-300", "agent_id": "codex-9", "status": "active"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(bus_message, "ROOT", root)
    monkeypatch.setattr(bus_message, "MESSAGES_DIR", messages_dir)
    monkeypatch.setattr(bus_message, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(bus_message, "MANIFEST_PATH", manifest)
    return messages_dir


def test_teof_bus_message_records_entry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    messages_dir = _setup_env(tmp_path, monkeypatch)

    exit_code = bootloader.main(
        [
            "bus_message",
            "--task",
            "QUEUE-300",
            "--type",
            "status",
            "--summary",
            "hello world",
        ]
    )

    assert exit_code == 0
    payload = json.loads((messages_dir / "QUEUE-300.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert payload["summary"] == "hello world"
    assert payload["from"] == "codex-9"
