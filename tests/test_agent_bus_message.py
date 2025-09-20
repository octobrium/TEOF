import json
from pathlib import Path

import pytest

from tools.agent import bus_message


def _configure_paths(tmp_path, monkeypatch):
    messages_dir = tmp_path / "messages"
    claims_dir = tmp_path / "claims"
    report_dir = tmp_path / "_report" / "agent"
    monkeypatch.setattr(bus_message, "MESSAGES_DIR", messages_dir)
    monkeypatch.setattr(bus_message, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(bus_message, "AGENT_REPORT_DIR", report_dir)
    monkeypatch.setattr(bus_message, "MANIFEST_PATH", tmp_path / "manifest.json")
    messages_dir.mkdir(parents=True, exist_ok=True)
    claims_dir.mkdir(parents=True, exist_ok=True)
    return messages_dir, claims_dir, report_dir


def _write_manifest(tmp_path: Path, agent_id: str = "codex-2") -> None:
    (tmp_path / "manifest.json").write_text(json.dumps({"agent_id": agent_id}), encoding="utf-8")


def _write_claim(claims_dir: Path, task_id: str, agent_id: str, status: str = "active") -> None:
    payload = {
        "task_id": task_id,
        "agent_id": agent_id,
        "status": status,
        "branch": f"agent/{agent_id}/{task_id.lower()}",
        "claimed_at": "2025-09-18T00:00:00Z",
    }
    (claims_dir / f"{task_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_bus_message_appends_jsonl(tmp_path, monkeypatch, capsys):
    messages_dir, claims_dir, _ = _configure_paths(tmp_path, monkeypatch)
    _write_manifest(tmp_path)
    _write_claim(claims_dir, "QUEUE-005", "codex-2")

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
    _configure_paths(tmp_path, monkeypatch)

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


def test_bus_message_requires_claim(tmp_path, monkeypatch):
    _, _, report_dir = _configure_paths(tmp_path, monkeypatch)
    _write_manifest(tmp_path)

    with pytest.raises(SystemExit) as exc:
        bus_message.main(
            [
                "--task",
                "QUEUE-123",
                "--type",
                "status",
                "--summary",
                "missing claim",
            ]
        )

    message = str(exc.value)
    assert "QUEUE-123" in message
    errors_path = report_dir / "codex-2" / "errors.jsonl"
    assert errors_path.exists()
    entries = [json.loads(line) for line in errors_path.read_text(encoding="utf-8").splitlines() if line]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["agent_id"] == "codex-2"
    assert entry["event"] == "status"
    assert entry["task_id"] == "QUEUE-123"


def test_bus_message_rejects_foreign_claim(tmp_path, monkeypatch):
    _, claims_dir, report_dir = _configure_paths(tmp_path, monkeypatch)
    _write_manifest(tmp_path, agent_id="codex-4")
    _write_claim(claims_dir, "QUEUE-222", "codex-3")

    with pytest.raises(SystemExit) as exc:
        bus_message.main(
            [
                "--task",
                "QUEUE-222",
                "--type",
                "note",
                "--summary",
                "should fail",
                "--agent",
                "codex-4",
            ]
        )

    message = str(exc.value)
    assert "claimed by codex-3" in message
    errors_path = report_dir / "codex-4" / "errors.jsonl"
    assert errors_path.exists()
    payloads = [json.loads(line) for line in errors_path.read_text(encoding="utf-8").splitlines() if line]
    assert payloads[0]["claim_owner"] == "codex-3"


def test_bus_message_allows_terminal_claim(tmp_path, monkeypatch):
    messages_dir, claims_dir, _ = _configure_paths(tmp_path, monkeypatch)
    _write_manifest(tmp_path, agent_id="codex-manager")
    _write_claim(claims_dir, "QUEUE-777", "codex-3", status="done")

    rc = bus_message.main(
        [
            "--task",
            "QUEUE-777",
            "--type",
            "status",
            "--summary",
            "post completion",
            "--agent",
            "codex-manager",
        ]
    )
    assert rc == 0
    assert (messages_dir / "QUEUE-777.jsonl").exists()


def test_bus_message_rejects_agent_mismatch(tmp_path, monkeypatch):
    _, claims_dir, report_dir = _configure_paths(tmp_path, monkeypatch)
    _write_manifest(tmp_path, agent_id="codex-1")
    _write_claim(claims_dir, "QUEUE-010", "codex-1")

    with pytest.raises(SystemExit) as exc:
        bus_message.main(
            [
                "--task",
                "QUEUE-010",
                "--type",
                "status",
                "--summary",
                "should detect mismatch",
                "--agent",
                "codex-2",
            ]
        )

    message = str(exc.value)
    assert "agent mismatch" in message
    # No new error entry should appear for codex-2 because the guard fires first.
    assert not (report_dir / "codex-2").exists()


def test_bus_message_allows_explicit_agent_without_manifest(tmp_path, monkeypatch):
    messages_dir, claims_dir, _ = _configure_paths(tmp_path, monkeypatch)
    _write_claim(claims_dir, "QUEUE-020", "codex-5")

    exit_code = bus_message.main(
        [
            "--task",
            "QUEUE-020",
            "--type",
            "note",
            "--summary",
            "explicit agent",
            "--agent",
            "codex-5",
        ]
    )

    assert exit_code == 0
    payload = json.loads((messages_dir / "QUEUE-020.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert payload["from"] == "codex-5"
