from pathlib import Path

import pytest

from tools.autonomy import manager_service as service


@pytest.fixture(autouse=True)
def patch_session(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(service.session_guard, "resolve_agent_id", lambda explicit: "codex-4")
    monkeypatch.setattr(service.session_guard, "ensure_recent_session", lambda *a, **k: None)


def test_dry_run(monkeypatch: pytest.MonkeyPatch, capsys):
    called = []

    def fake_run(manager_agent, worker_agent, allow_worker_stale, dry_run):
        called.append((manager_agent, worker_agent, dry_run))
        return {"worker": worker_agent, "exit_code": 0}

    monkeypatch.setattr(service, "_run_worker", fake_run)
    exit_code = service.main(["--workers", "codex-4", "codex-5", "--dry-run", "--max-rounds", "1"])
    assert exit_code == 0
    assert called == [("codex-4", "codex-4", True), ("codex-4", "codex-5", True)]
    assert "manager_service" not in capsys.readouterr().out


def test_manager_logs_receipt(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    receipts = []

    def fake_run(manager_agent, worker_agent, allow_worker_stale, dry_run):
        return {"worker": worker_agent, "exit_code": 0}

    def fake_write(agent, payload):
        receipts.append(payload)
        return tmp_path / "receipt.json"

    monkeypatch.setattr(service, "_run_worker", fake_run)
    monkeypatch.setattr(service, "_write_receipt", fake_write)

    exit_code = service.main(["--workers", "codex-4", "--log", "--max-rounds", "1"])
    assert exit_code == 0
    assert receipts and receipts[0]["results"][0]["worker"] == "codex-4"
