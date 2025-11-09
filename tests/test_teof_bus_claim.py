from __future__ import annotations

import json
from pathlib import Path

import pytest

import teof.bootloader as bootloader
from tools.agent import bus_claim, session_guard


def _setup_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path
    claims_dir = root / "_bus" / "claims"
    assignments_dir = root / "_bus" / "assignments"
    session_dir = root / "_report" / "session"
    agent_dir = root / "_report" / "agent"
    claims_dir.mkdir(parents=True, exist_ok=True)
    assignments_dir.mkdir(parents=True, exist_ok=True)
    session_dir.mkdir(parents=True, exist_ok=True)
    agent_dir.mkdir(parents=True, exist_ok=True)

    manifest = root / "AGENT_MANIFEST.json"
    manifest.write_text(json.dumps({"agent_id": "codex-test"}), encoding="utf-8")

    monkeypatch.setattr(bus_claim, "ROOT", root)
    monkeypatch.setattr(bus_claim, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(bus_claim, "ASSIGNMENTS_DIR", assignments_dir)
    monkeypatch.setattr(bus_claim, "MANIFEST_PATH", manifest)

    monkeypatch.setattr(session_guard, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(session_guard, "SESSION_DIR", session_dir)
    monkeypatch.setattr(session_guard, "AGENT_REPORT_DIR", agent_dir)
    monkeypatch.setenv("TEOF_SESSION_GUARD_DISABLED", "1")


def test_teof_bus_claim_creates_claim(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _setup_env(tmp_path, monkeypatch)

    exit_code = bootloader.main(
        [
            "bus_claim",
            "claim",
            "--task",
            "QUEUE-999",
            "--agent",
            "codex-test",
            "--status",
            "active",
            "--plan",
            "PLAN-XYZ",
            "--branch",
            "agent/codex-test/queue-999",
            "--allow-unassigned",
        ]
    )

    assert exit_code == 0
    claim_path = tmp_path / "_bus" / "claims" / "QUEUE-999.json"
    assert claim_path.exists()
    payload = json.loads(claim_path.read_text(encoding="utf-8"))
    assert payload["agent_id"] == "codex-test"
    assert payload["status"] == "active"


def test_teof_bus_claim_release(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _setup_env(tmp_path, monkeypatch)
    claim_path = tmp_path / "_bus" / "claims" / "QUEUE-500.json"
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    claim_path.write_text(
        json.dumps(
            {
                "task_id": "QUEUE-500",
                "agent_id": "codex-test",
                "branch": "agent/codex-test/queue-500",
                "status": "active",
                "plan_id": "PLAN-500",
                "claimed_at": "2025-11-09T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    exit_code = bootloader.main(
        [
            "bus_claim",
            "release",
            "--task",
            "QUEUE-500",
            "--agent",
            "codex-test",
            "--status",
            "done",
        ]
    )

    assert exit_code == 0
    payload = json.loads(claim_path.read_text(encoding="utf-8"))
    assert payload["status"] == "done"
    assert "released_at" in payload
