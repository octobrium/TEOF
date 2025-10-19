import json
from pathlib import Path

import pytest

from tools.autonomy import coordinator_guard as guard


@pytest.fixture(autouse=True)
def patch_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    monkeypatch.setattr(guard, "STATE_PATH", tmp_path / "_report" / "agent")


def test_guard_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    plan = {"plan_id": "PLAN-1", "summary": "Coordinator", "systemic_targets": ["S1"], "layer_targets": ["L5"]}
    step = {"id": "step-4", "title": "Guard", "notes": "Ensure guard."}

    monkeypatch.setattr(guard.session_guard, "resolve_agent_id", lambda explicit: "codex-4")
    monkeypatch.setattr(guard.session_guard, "ensure_recent_session", lambda *a, **k: None)
    monkeypatch.setattr(guard, "_load_plan", lambda plan_id: plan)
    monkeypatch.setattr(guard, "_select_step", lambda _plan, _step: step)

    manifest_path = tmp_path / "manifest.json"

    def fake_load_manifest(agent_id: str, _plan, _step):
        manifest_path.write_text("{}", encoding="utf-8")
        return manifest_path

    monkeypatch.setattr(guard, "_load_manifest", fake_load_manifest)
    monkeypatch.setattr(guard, "_systemic_check", lambda *_: {"verdict": "ready", "scores": {}, "total": 10})
    monkeypatch.setattr(guard, "_run_scan", lambda label, force=False: {"label": label, "status": "ok", "triggered": True, "exit_code": 0})
    monkeypatch.setattr(guard.coordinator_worker, "main", lambda args: 0)

    bus_calls = []
    monkeypatch.setattr(guard, "_log_bus", lambda *a, **k: bus_calls.append((a, k)))

    exit_code = guard.main(["--plan", "PLAN-1", "--step", "step-4", "--execute"])
    assert exit_code == 0

    state_path = guard._state_path("codex-4")  # pylint: disable=protected-access
    assert state_path.exists()

    payload = state_path.read_text(encoding="utf-8")
    assert "circuit_breaker" in payload
    if bus_calls:
        assert bus_calls[0][0][2] == "info"


def test_guard_systemic_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    plan = {"plan_id": "PLAN-2", "summary": "Coordinator", "systemic_targets": ["S1"], "layer_targets": ["L5"]}
    step = {"id": "step-4", "title": "Guard", "notes": "Ensure guard."}

    monkeypatch.setattr(guard.session_guard, "resolve_agent_id", lambda explicit: "codex-4")
    monkeypatch.setattr(guard.session_guard, "ensure_recent_session", lambda *a, **k: None)
    monkeypatch.setattr(guard, "_load_plan", lambda plan_id: plan)
    monkeypatch.setattr(guard, "_select_step", lambda _plan, _step: step)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(guard, "_load_manifest", lambda *a, **k: manifest_path)
    monkeypatch.setattr(guard, "_systemic_check", lambda *_: {"verdict": "review", "scores": {}, "total": 4})
    monkeypatch.setattr(guard, "_run_scan", lambda label, force=False: {"label": label, "status": "skipped", "triggered": False, "exit_code": None})

    worker_called = []
    monkeypatch.setattr(guard.coordinator_worker, "main", lambda args: worker_called.append(args) or 0)
    monkeypatch.setattr(guard, "_log_bus", lambda *a, **k: None)

    exit_code = guard.main(["--plan", "PLAN-2", "--step", "step-4", "--execute"])
    assert exit_code == 2
    assert not worker_called

    state_path = guard._state_path("codex-4")  # pylint: disable=protected-access
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["circuit_breaker"]["active"] is True
    assert "systemic_verdict" in payload["circuit_breaker"]["reason"]
