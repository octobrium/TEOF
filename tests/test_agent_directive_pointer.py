import json
from pathlib import Path

import pytest

from tools.agent import bus_message, directive_pointer


def _configure_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    bus_dir = tmp_path / "bus"
    messages_dir = bus_dir / "messages"
    claims_dir = bus_dir / "claims"
    report_dir = tmp_path / "_report" / "agent"
    manifest_path = tmp_path / "manifest.json"

    messages_dir.mkdir(parents=True, exist_ok=True)
    claims_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(bus_message, "MESSAGES_DIR", messages_dir)
    monkeypatch.setattr(bus_message, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(bus_message, "AGENT_REPORT_DIR", report_dir)
    monkeypatch.setattr(bus_message, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(bus_message, "record_usage", lambda *args, **kwargs: None)

    monkeypatch.setattr(directive_pointer, "ROOT", tmp_path)
    monkeypatch.setattr(bus_message, "ROOT", tmp_path)
    monkeypatch.setattr(directive_pointer, "record_usage", lambda *args, **kwargs: None)

    return messages_dir, claims_dir, manifest_path


def _write_manifest(path: Path, agent_id: str = "codex-1") -> None:
    path.write_text(json.dumps({"agent_id": agent_id}), encoding="utf-8")


def _write_claim(claims_dir: Path, task_id: str, agent_id: str, *, status: str = "active") -> None:
    payload = {
        "task_id": task_id,
        "agent_id": agent_id,
        "status": status,
        "branch": f"agent/{agent_id}/{task_id.lower()}",
        "claimed_at": "2025-09-20T00:00:00Z",
    }
    (claims_dir / f"{task_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_directive_pointer_logs_directive_and_pointer(tmp_path, monkeypatch, capsys):
    messages_dir, claims_dir, manifest_path = _configure_paths(tmp_path, monkeypatch)
    _write_manifest(manifest_path)
    _write_claim(claims_dir, "BUS-COORD-9001", "codex-1")
    _write_claim(claims_dir, "manager-report", "codex-1")

    rc = directive_pointer.main(
        [
            "--task",
            "BUS-COORD-9001",
            "--summary",
            "Repo hygiene directive",
            "--plan",
            "2025-09-20-manager-directive-pointer",
        ]
    )
    assert rc == 0

    captured = capsys.readouterr()
    assert "BUS-COORD-9001" in captured.out
    directive_messages = _load_jsonl(messages_dir / "BUS-COORD-9001.jsonl")
    directive_payload = directive_messages[0]
    assert directive_payload["type"] == "directive"
    assert directive_payload["summary"] == "Repo hygiene directive"
    assert directive_payload["meta"]["plan_id"] == "2025-09-20-manager-directive-pointer"

    pointer_messages = _load_jsonl(messages_dir / "manager-report.jsonl")
    pointer = pointer_messages[0]
    assert pointer["summary"] == "Directive BUS-COORD-9001 posted"
    assert pointer["meta"]["directive"] == "BUS-COORD-9001"
    assert pointer["meta"]["plan_id"] == "2025-09-20-manager-directive-pointer"


def test_directive_pointer_allows_custom_pointer_fields(tmp_path, monkeypatch):
    messages_dir, claims_dir, manifest_path = _configure_paths(tmp_path, monkeypatch)
    _write_manifest(manifest_path, agent_id="codex-4")
    _write_claim(claims_dir, "BUS-COORD-9002", "codex-4")
    _write_claim(claims_dir, "manager-report", "codex-4")

    rc = directive_pointer.main(
        [
            "--task",
            "BUS-COORD-9002",
            "--summary",
            "Automation split",
            "--note",
            "Split responsibilities",
            "--agent",
            "codex-4",
            "--plan",
            "2025-09-20-manager-directive-pointer",
            "--receipt",
            "_report/directive.md",
            "--meta",
            "severity=high",
            "--pointer-summary",
            "Directive BUS-COORD-9002 open",
            "--pointer-note",
            "Review BUS-COORD-9002",
            "--pointer-type",
            "note",
            "--pointer-receipt",
            "_report/pointer.md",
            "--pointer-meta",
            "channel=manager",
        ]
    )
    assert rc == 0

    directive_payload = _load_jsonl(messages_dir / "BUS-COORD-9002.jsonl")[0]
    assert directive_payload["meta"]["severity"] == "high"
    assert directive_payload["receipts"] == ["_report/directive.md"]

    pointer_payload = _load_jsonl(messages_dir / "manager-report.jsonl")[0]
    assert pointer_payload["type"] == "note"
    assert pointer_payload["summary"] == "Directive BUS-COORD-9002 open"
    assert pointer_payload["note"] == "Review BUS-COORD-9002"
    assert pointer_payload["receipts"] == ["_report/pointer.md"]
    assert pointer_payload["meta"]["directive"] == "BUS-COORD-9002"
    assert pointer_payload["meta"]["channel"] == "manager"
