from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from tools.agent import claim_seed
from tools.receipts import scaffold as receipt_scaffold

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def test_seed_creates_claim(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(claim_seed, "CLAIMS_DIR", tmp_path)
    monkeypatch.setattr(receipt_scaffold, "ROOT", tmp_path)
    monkeypatch.setattr(receipt_scaffold, "REPORT_ROOT", tmp_path / "_report" / "agent")
    now = "2025-09-18T20:40:00Z"
    monkeypatch.setattr(claim_seed, "iso_now", lambda: now)
    exit_code = claim_seed.main(
        [
            "--task",
            "QUEUE-200",
            "--agent",
            "codex-4",
            "--plan",
            "2025-plan",
            "--branch",
            "agent/codex-4/queue-200",
            "--notes",
            "seeded by test",
        ]
    )
    assert exit_code == 0
    payload = json.loads((tmp_path / "QUEUE-200.json").read_text(encoding="utf-8"))
    assert payload["agent_id"] == "codex-4"
    assert payload["plan_id"] == "2025-plan"
    assert payload["status"] == "paused"
    assert payload["claimed_at"] == now


def test_seed_rejects_other_active_claim(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(claim_seed, "CLAIMS_DIR", tmp_path)
    monkeypatch.setattr(receipt_scaffold, "ROOT", tmp_path)
    monkeypatch.setattr(receipt_scaffold, "REPORT_ROOT", tmp_path / "_report" / "agent")
    (tmp_path / "QUEUE-201.json").write_text(
        json.dumps(
            {
                "agent_id": "codex-2",
                "task_id": "QUEUE-201",
                "status": "active",
            }
        )
    )
    with pytest.raises(SystemExit):
        claim_seed.main(["--task", "QUEUE-201", "--agent", "codex-4"])


def test_seed_overrides_terminal_claim(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(claim_seed, "CLAIMS_DIR", tmp_path)
    monkeypatch.setattr(receipt_scaffold, "ROOT", tmp_path)
    monkeypatch.setattr(receipt_scaffold, "REPORT_ROOT", tmp_path / "_report" / "agent")
    (tmp_path / "QUEUE-202.json").write_text(
        json.dumps(
            {
                "agent_id": "codex-2",
                "task_id": "QUEUE-202",
                "status": "done",
                "released_at": "2025-09-18T19:00:00Z",
            }
        )
    )
    claim_seed.main(["--task", "QUEUE-202", "--agent", "codex-4", "--status", "paused"])
    payload = json.loads((tmp_path / "QUEUE-202.json").read_text(encoding="utf-8"))
    assert payload["agent_id"] == "codex-4"
    assert payload["status"] == "paused"


def test_seed_with_scaffold(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.setattr(claim_seed, "CLAIMS_DIR", tmp_path)
    monkeypatch.setattr(receipt_scaffold, "ROOT", tmp_path)
    monkeypatch.setattr(receipt_scaffold, "REPORT_ROOT", tmp_path / "_report" / "agent")
    now = "2025-09-20T10:00:00Z"
    monkeypatch.setattr(claim_seed, "iso_now", lambda: now)

    rc = claim_seed.main(
        [
            "--task",
            "QUEUE-300",
            "--agent",
            "codex-5",
            "--plan",
            "2025-09-20-receipt-scaffold-v2",
            "--branch",
            "agent/codex-5/queue-300",
            "--scaffold",
        ]
    )
    assert rc == 0

    receipt_dir = tmp_path / "_report" / "agent" / "codex-5" / "2025-09-20-receipt-scaffold-v2"
    assert (receipt_dir / "actions.json").exists()
    claim_stub = json.loads((receipt_dir / "claim.json").read_text(encoding="utf-8"))
    assert claim_stub["task_id"] == "QUEUE-300"
    assert claim_stub["branch"] == "agent/codex-5/queue-300"

    out = capsys.readouterr().out
    assert "Created" in out
