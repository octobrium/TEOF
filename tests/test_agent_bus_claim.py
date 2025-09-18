import json
from pathlib import Path

import pytest

from tools.agent import bus_claim


def setup_bus_claim(monkeypatch, tmp_path):
    claims_dir = tmp_path / "claims"
    manifest_path = tmp_path / "AGENT_MANIFEST.json"
    monkeypatch.setattr(bus_claim, "ROOT", tmp_path)
    monkeypatch.setattr(bus_claim, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(bus_claim, "MANIFEST_PATH", manifest_path)
    return claims_dir, manifest_path


def load_claim(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_bus_claim_creates_claim_file(monkeypatch, tmp_path):
    claims_dir, _ = setup_bus_claim(monkeypatch, tmp_path)

    rc = bus_claim.main([
        "claim",
        "--task",
        "QUEUE-101",
        "--agent",
        "codex-3",
        "--plan",
        "plan-queue-101",
    ])
    assert rc == 0

    claim_path = claims_dir / "QUEUE-101.json"
    assert claim_path.exists()
    data = load_claim(claim_path)
    assert data["task_id"] == "QUEUE-101"
    assert data["agent_id"] == "codex-3"
    assert data["status"] == "active"
    assert data["branch"] == "agent/codex-3/queue-101"
    assert data["plan_id"] == "plan-queue-101"
    assert "claimed_at" in data


def test_bus_claim_conflict_detected(monkeypatch, tmp_path):
    claims_dir, _ = setup_bus_claim(monkeypatch, tmp_path)
    claims_dir.mkdir(parents=True, exist_ok=True)
    existing = {
        "task_id": "QUEUE-101",
        "agent_id": "codex-1",
        "branch": "agent/codex-1/queue-101",
        "status": "active",
        "claimed_at": "2025-09-17T00:00:00Z",
    }
    (claims_dir / "QUEUE-101.json").write_text(json.dumps(existing), encoding="utf-8")

    with pytest.raises(SystemExit):
        bus_claim.main([
            "claim",
            "--task",
            "QUEUE-101",
            "--agent",
            "codex-3",
        ])


def test_bus_claim_release_updates_status(monkeypatch, tmp_path):
    claims_dir, _ = setup_bus_claim(monkeypatch, tmp_path)

    bus_claim.main([
        "claim",
        "--task",
        "QUEUE-200",
        "--agent",
        "codex-3",
    ])

    rc = bus_claim.main([
        "release",
        "--task",
        "QUEUE-200",
        "--agent",
        "codex-3",
        "--status",
        "done",
        "--notes",
        "Completed tests",
    ])
    assert rc == 0

    claim_path = claims_dir / "QUEUE-200.json"
    data = load_claim(claim_path)
    assert data["status"] == "done"
    assert data["notes"] == "Completed tests"
    assert "released_at" in data
