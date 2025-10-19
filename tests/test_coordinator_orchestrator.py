from pathlib import Path

import pytest

from tools.autonomy import coordinator_orchestrator as orchestrator


@pytest.fixture(autouse=True)
def patch_session(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(orchestrator.session_guard, "resolve_agent_id", lambda explicit: "codex-4")
    monkeypatch.setattr(orchestrator.session_guard, "ensure_recent_session", lambda *a, **k: None)


def test_dry_run(capsys):
    exit_code = orchestrator.main(["--plan", "PLAN", "--step", "step-1", "--dry-run"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "would run guard" in out


def test_execute_invokes_guard(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    def fake_guard(args):
        captured["args"] = args
        return 0

    monkeypatch.setattr(orchestrator, "coordinator_guard", type("G", (), {"main": staticmethod(fake_guard)}))
    monkeypatch.setattr(orchestrator, "bus_claim", type("B", (), {"main": staticmethod(lambda args: captured.setdefault("claim", args))}))

    exit_code = orchestrator.main([
        "--plan",
        "PLAN",
        "--step",
        "step-1",
        "--task-id",
        "TASK-1",
        "--branch",
        "agent/codex-4/test",
        "--allow-worker-stale",
    ])
    assert exit_code == 0
    assert captured["claim"][2] == "TASK-1"
    assert "--allow-worker-stale" in captured["args"]
