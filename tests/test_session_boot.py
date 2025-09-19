import json
from pathlib import Path

from tools.agent import session_boot, session_sync


class FakeSync:
    def __init__(self):
        self.called = False
        self.allow_dirty = None
        self.result = session_sync.SyncResult(
            changed=False,
            fetch_output="",
            pull_output="",
            dirty=False,
        )

    def __call__(self, *, allow_dirty):
        self.called = True
        self.allow_dirty = allow_dirty
        return self.result


def _setup_env(monkeypatch, tmp_path: Path, *, agent_id: str = "codex-3") -> Path:
    events_path = tmp_path / "events.jsonl"
    claims_dir = tmp_path / "claims"
    claims_dir.mkdir()
    manifest_path = tmp_path / "AGENT_MANIFEST.json"
    manifest_path.write_text(json.dumps({"agent_id": agent_id}), encoding="utf-8")
    monkeypatch.setattr(session_boot, "EVENT_LOG", events_path)
    monkeypatch.setattr(session_boot, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(session_boot, "MANIFEST_PATH", manifest_path)
    return events_path


def test_session_boot_runs_sync_before_handshake(monkeypatch, tmp_path):
    events_path = _setup_env(monkeypatch, tmp_path)
    sync = FakeSync()
    monkeypatch.setattr(session_boot.session_sync, "run_sync", sync)

    exit_code = session_boot.main(["--agent", "codex-3"])

    assert exit_code == 0
    assert sync.called is True
    assert sync.allow_dirty is False
    payloads = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    assert payloads, "handshake event should be recorded"
    assert payloads[-1]["agent_id"] == "codex-3"


def test_session_boot_no_sync_flag(monkeypatch, tmp_path):
    events_path = _setup_env(monkeypatch, tmp_path)
    sync = FakeSync()
    monkeypatch.setattr(session_boot.session_sync, "run_sync", sync)

    exit_code = session_boot.main(["--agent", "codex-3", "--no-sync"])

    assert exit_code == 0
    assert sync.called is False
    assert events_path.exists()


def test_session_boot_sync_failure(monkeypatch, tmp_path, capsys):
    events_path = _setup_env(monkeypatch, tmp_path)

    def fail_sync(**_):
        raise session_sync.SessionSyncError("boom")

    monkeypatch.setattr(session_boot.session_sync, "run_sync", fail_sync)

    exit_code = session_boot.main(["--agent", "codex-3"])

    assert exit_code == 1
    assert not events_path.exists()
    captured = capsys.readouterr()
    assert "Session sync failed" in captured.err


def test_session_boot_allows_dirty(monkeypatch, tmp_path):
    events_path = _setup_env(monkeypatch, tmp_path)

    def dirty_sync(*, allow_dirty):
        assert allow_dirty is True
        return session_sync.SyncResult(
            changed=False,
            fetch_output="",
            pull_output="",
            dirty=True,
        )

    monkeypatch.setattr(session_boot.session_sync, "run_sync", dirty_sync)

    exit_code = session_boot.main(["--agent", "codex-3", "--sync-allow-dirty"])

    assert exit_code == 0
    assert events_path.exists()
