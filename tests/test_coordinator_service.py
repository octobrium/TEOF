from pathlib import Path

import pytest

from tools.autonomy import coordinator_service as service


@pytest.fixture(autouse=True)
def patch_session(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(service.session_guard, "resolve_agent_id", lambda explicit: "codex-4")
    monkeypatch.setattr(service.session_guard, "ensure_recent_session", lambda *a, **k: None)


def test_service_runs_once(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    called = {}

    def fake_loop(args):
        called["args"] = args
        return 0

    monkeypatch.setattr(service, "_run_loop", fake_loop)
    monkeypatch.setattr(service, "_write_log", lambda *a, **k: tmp_path / "dummy.json")

    exit_code = service.main(["--once", "--log"])
    assert exit_code == 0
    assert "--iterations" in called["args"]
