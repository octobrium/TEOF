from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tools.consensus import receipts


def test_append_receipt_creates_file(tmp_path: Path) -> None:
    out = tmp_path / "out.jsonl"
    path = receipts.append_receipt(
        decision_id="DEC-1",
        summary="Consensus approved",
        agent_id="agent-1",
        event="complete",
        receipts=["_report/agent/a.txt"],
        metadata={"task_id": "QUEUE-031"},
        output=out,
    )
    assert path == out.resolve()
    content = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(content) == 1
    payload = json.loads(content[0])
    assert payload["decision_id"] == "DEC-1"
    assert payload["receipts"] == ["_report/agent/a.txt"]
    assert payload["meta"]["task_id"] == "QUEUE-031"


def test_bus_event_integration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Reload module to avoid sharing global state
    bus_event = importlib.import_module("tools.agent.bus_event")
    importlib.reload(bus_event)

    monkeypatch.setattr(bus_event, "ROOT", tmp_path)
    monkeypatch.setattr(bus_event, "EVENT_LOG", tmp_path / "_bus" / "events" / "events.jsonl")
    monkeypatch.setattr(bus_event, "CLAIMS_DIR", tmp_path / "_bus" / "claims")
    monkeypatch.setattr(bus_event, "AGENT_REPORT_DIR", tmp_path / "_report" / "agent")
    monkeypatch.setattr(bus_event, "MANIFEST_PATH", tmp_path / "AGENT_MANIFEST.json")
    monkeypatch.setattr(receipts, "ROOT", tmp_path)
    monkeypatch.setattr(receipts, "DEFAULT_DIR", tmp_path / "_report" / "consensus")

    manifest = tmp_path / "AGENT_MANIFEST.json"
    manifest.write_text(json.dumps({"agent_id": "codex-test"}), encoding="utf-8")

    claims_dir = tmp_path / "_bus" / "claims"
    claims_dir.mkdir(parents=True, exist_ok=True)
    (claims_dir / "QUEUE-031.json").write_text(
        json.dumps({"agent_id": "codex-test", "status": "active"}),
        encoding="utf-8",
    )

    exit_code = bus_event.main(
        [
            "log",
            "--event",
            "complete",
            "--summary",
            "Consensus closed",
            "--task",
            "QUEUE-031",
            "--consensus-decision",
            "DEC-99",
        ]
    )
    assert exit_code == 0

    log_path = tmp_path / "_bus" / "events" / "events.jsonl"
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    payload = json.loads(lines[-1])
    assert payload["receipts"]
    receipt_path = tmp_path / payload["receipts"][0]
    assert receipt_path.exists()
    receipt_payload = json.loads(receipt_path.read_text(encoding="utf-8").strip())
    assert receipt_payload["decision_id"] == "DEC-99"
    assert receipt_payload["agent_id"] == "codex-test"
