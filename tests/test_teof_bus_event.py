from pathlib import Path

import json
import pytest

import teof.bootloader as bootloader
from tools.agent import bus_event, session_guard


def _setup_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = tmp_path / "AGENT_MANIFEST.json"
    manifest.write_text(json.dumps({"agent_id": "codex-9"}), encoding="utf-8")
    monkeypatch.setattr(bus_event, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(session_guard, "MANIFEST_PATH", manifest)
    claims_dir = tmp_path / "_bus" / "claims"
    claims_dir.mkdir(parents=True, exist_ok=True)
    (claims_dir / "QUEUE-200.json").write_text(
        json.dumps({"task_id": "QUEUE-200", "agent_id": "codex-9", "status": "active"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(bus_event, "CLAIMS_DIR", claims_dir)
    report_dir = tmp_path / "_report" / "agent"
    monkeypatch.setattr(bus_event, "AGENT_REPORT_DIR", report_dir)
    monkeypatch.setattr(bus_event, "ROOT", tmp_path)


def test_teof_bus_event_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup_manifest(tmp_path, monkeypatch)
    events_log = tmp_path / "_bus" / "events" / "events.jsonl"
    monkeypatch.setattr(bus_event, "EVENT_LOG", events_log)

    exit_code = bootloader.main(
        [
            "bus_event",
            "log",
            "--event",
            "status",
            "--summary",
            "working",
            "--task",
            "QUEUE-200",
        ]
    )

    assert exit_code == 0
    content = events_log.read_text(encoding="utf-8").strip().splitlines()
    assert content
    payload = json.loads(content[-1])
    assert payload["event"] == "status"
    assert payload["summary"] == "working"
    assert payload["task_id"] == "QUEUE-200"
    assert payload["agent_id"] == "codex-9"
