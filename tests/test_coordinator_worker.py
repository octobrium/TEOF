import json
from pathlib import Path

import pytest

from tools.autonomy import coordinator_worker as worker


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.fixture(autouse=True)
def patch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(worker, "ROOT", tmp_path)
    monkeypatch.setattr(worker, "RUNS_BASE", tmp_path / "_report" / "agent")


def test_worker_dry_run_lists_commands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    manifest = {
        "plan": {"id": "PLAN-1"},
        "step": {"id": "step-1"},
        "commands": [
            {"label": "status", "description": "status", "cmd": ["echo", "status"]}
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    _write(manifest_path, manifest)

    monkeypatch.setattr(worker.session_guard, "resolve_agent_id", lambda explicit: "codex-4")
    monkeypatch.setattr(worker.session_guard, "ensure_recent_session", lambda *a, **k: None)

    exit_code = worker.main([str(manifest_path)])
    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "dry-run" in stdout
    assert "echo status" in stdout


def test_worker_execute_runs_command_and_writes_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    manifest = {
        "plan": {"id": "PLAN-2"},
        "step": {"id": "step-2"},
        "commands": [
            {"label": "print", "description": "print", "cmd": ["python3", "-c", "print('ok')"]}
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    _write(manifest_path, manifest)

    monkeypatch.setattr(worker.session_guard, "resolve_agent_id", lambda explicit: "codex-4")
    monkeypatch.setattr(worker.session_guard, "ensure_recent_session", lambda *a, **k: None)

    exit_code = worker.main([str(manifest_path), "--execute"])
    assert exit_code == 0

    runs_dir = tmp_path / "_report" / "agent" / "codex-4" / "PLAN-2" / "runs"
    receipts = list(runs_dir.glob("run-*.json"))
    assert receipts, "worker should write a run receipt"
    data = json.loads(receipts[0].read_text(encoding="utf-8"))
    assert data["agent_id"] == "codex-4"
    assert data["plan"]["id"] == "PLAN-2"
    assert data["executed"][0]["status"] == "ok"
