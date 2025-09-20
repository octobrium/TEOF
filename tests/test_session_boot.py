import json
from pathlib import Path
from typing import List, Optional

from tools.agent import session_boot, session_sync


class FakeDashboard:
    def __init__(self):
        self.calls = []

    def __call__(
        self,
        *,
        root,
        fmt,
        manager_window,
        agent_window,
        directive_limit,
        output_path,
        compact,
        stream,
    ):
        self.calls.append(
            {
                "root": root,
                "fmt": fmt,
                "manager_window": manager_window,
                "agent_window": agent_window,
                "directive_limit": directive_limit,
                "output_path": output_path,
                "compact": compact,
            }
        )
        if stream is not None:
            stream.write("{}")
        output_path.write_text("{}", encoding="utf-8")
        return {}


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


def _setup_env(
    monkeypatch,
    tmp_path: Path,
    *,
    agent_id: str = "codex-3",
    manager_entries: Optional[List[str]] = None,
):
    root = tmp_path
    monkeypatch.setattr(session_boot, "ROOT", root)

    events_path = root / "_bus" / "events" / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    claims_dir = root / "_bus" / "claims"
    claims_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "AGENT_MANIFEST.json"
    manifest_path.write_text(json.dumps({"agent_id": agent_id}), encoding="utf-8")
    manager_log = root / "_bus" / "messages" / "manager-report.jsonl"
    manager_log.parent.mkdir(parents=True, exist_ok=True)
    if manager_entries is None:
        manager_entries = ["{\"ts\": \"2025-09-20T00:00:00Z\", \"note\": \"init\"}\n"]
    manager_log.write_text("".join(manager_entries), encoding="utf-8")

    monkeypatch.setattr(session_boot, "EVENT_LOG", events_path)
    monkeypatch.setattr(session_boot, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(session_boot, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(session_boot, "MANAGER_REPORT_LOG", manager_log)

    return events_path, manager_log


def test_session_boot_runs_sync_before_handshake(monkeypatch, tmp_path):
    events_path, _ = _setup_env(monkeypatch, tmp_path)
    sync = FakeSync()
    monkeypatch.setattr(session_boot.session_sync, "run_sync", sync)
    dashboard = FakeDashboard()
    monkeypatch.setattr(session_boot.coord_dashboard, "run_report", dashboard)

    receipt_path = tmp_path / "dashboard.json"
    exit_code = session_boot.main([
        "--agent",
        "codex-3",
        "--dashboard-receipt",
        str(receipt_path),
    ])

    assert exit_code == 0
    assert sync.called is True
    assert sync.allow_dirty is False
    payloads = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    assert payloads, "handshake event should be recorded"
    assert payloads[-1]["agent_id"] == "codex-3"
    assert receipt_path.exists()
    assert dashboard.calls, "coord_dashboard should run by default"


def test_session_boot_no_sync_flag(monkeypatch, tmp_path):
    events_path, _ = _setup_env(monkeypatch, tmp_path)
    sync = FakeSync()
    monkeypatch.setattr(session_boot.session_sync, "run_sync", sync)
    dashboard = FakeDashboard()
    monkeypatch.setattr(session_boot.coord_dashboard, "run_report", dashboard)

    exit_code = session_boot.main(["--agent", "codex-3", "--no-sync"])

    assert exit_code == 0
    assert sync.called is False
    assert events_path.exists()
    assert dashboard.calls, "Dashboard should still run when sync skipped"


def test_session_boot_sync_failure(monkeypatch, tmp_path, capsys):
    events_path, _ = _setup_env(monkeypatch, tmp_path)

    def fail_sync(**_):
        raise session_sync.SessionSyncError("boom")

    monkeypatch.setattr(session_boot.session_sync, "run_sync", fail_sync)

    exit_code = session_boot.main(["--agent", "codex-3"])

    assert exit_code == 1
    assert not events_path.exists()
    captured = capsys.readouterr()
    assert "Session sync failed" in captured.err


def test_session_boot_allows_dirty(monkeypatch, tmp_path):
    events_path, _ = _setup_env(monkeypatch, tmp_path)

    def dirty_sync(*, allow_dirty):
        assert allow_dirty is True
        return session_sync.SyncResult(
            changed=False,
            fetch_output="",
            pull_output="",
            dirty=True,
        )

    monkeypatch.setattr(session_boot.session_sync, "run_sync", dirty_sync)
    dashboard = FakeDashboard()
    monkeypatch.setattr(session_boot.coord_dashboard, "run_report", dashboard)

    exit_code = session_boot.main(["--agent", "codex-3", "--sync-allow-dirty"])

    assert exit_code == 0
    assert events_path.exists()
    assert dashboard.calls


def test_session_boot_allows_disabling_dashboard(monkeypatch, tmp_path):
    _setup_env(monkeypatch, tmp_path)
    sync = FakeSync()
    monkeypatch.setattr(session_boot.session_sync, "run_sync", sync)
    dashboard = FakeDashboard()
    monkeypatch.setattr(session_boot.coord_dashboard, "run_report", dashboard)

    exit_code = session_boot.main(["--agent", "codex-3", "--no-dashboard"])

    assert exit_code == 0
    assert not dashboard.calls


def test_session_boot_emits_bus_watch_hint(monkeypatch, tmp_path, capsys):
    _setup_env(monkeypatch, tmp_path)
    sync = FakeSync()
    monkeypatch.setattr(session_boot.session_sync, "run_sync", sync)
    dashboard = FakeDashboard()
    monkeypatch.setattr(session_boot.coord_dashboard, "run_report", dashboard)

    exit_code = session_boot.main(["--agent", "codex-3", "--no-dashboard"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "python -m tools.agent.bus_watch --task manager-report --follow --limit 20" in out


def test_session_boot_writes_manager_report_tail(monkeypatch, tmp_path):
    manager_entries = [
        '{"ts": "2025-09-20T21:30:00Z", "summary": "a"}\n',
        '{"ts": "2025-09-20T21:31:00Z", "summary": "b"}\n',
        '{"ts": "2025-09-20T21:32:00Z", "summary": "c"}\n',
    ]
    _events_path, manager_log = _setup_env(
        monkeypatch,
        tmp_path,
        manager_entries=manager_entries,
    )

    sync = FakeSync()
    monkeypatch.setattr(session_boot.session_sync, "run_sync", sync)
    dashboard = FakeDashboard()
    monkeypatch.setattr(session_boot.coord_dashboard, "run_report", dashboard)

    exit_code = session_boot.main(
        [
            "--agent",
            "codex-3",
            "--no-dashboard",
            "--manager-report-tail-count",
            "2",
        ]
    )

    assert exit_code == 0
    tail_path = tmp_path / "_report" / "session" / "codex-3" / "manager-report-tail.txt"
    assert tail_path.exists()
    content = tail_path.read_text(encoding="utf-8")
    assert "requested_entries=2" in content
    assert "written_entries=2" in content
    assert manager_entries[-2].strip() in content
    assert manager_entries[-1].strip() in content
    assert manager_log.read_text(encoding="utf-8").strip().endswith("summary\": \"c\"}")


def test_session_boot_can_skip_manager_report_tail(monkeypatch, tmp_path):
    _events_path, _ = _setup_env(monkeypatch, tmp_path)
    sync = FakeSync()
    monkeypatch.setattr(session_boot.session_sync, "run_sync", sync)
    dashboard = FakeDashboard()
    monkeypatch.setattr(session_boot.coord_dashboard, "run_report", dashboard)

    exit_code = session_boot.main(
        [
            "--agent",
            "codex-3",
            "--no-dashboard",
            "--no-manager-report-tail",
        ]
    )

    assert exit_code == 0
    tail_path = tmp_path / "_report" / "session" / "codex-3" / "manager-report-tail.txt"
    assert not tail_path.exists()
