import pytest

from tools.agent import session_sync


class DummyResult:
    def __init__(self, *, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_run_sync_clean_repo(monkeypatch):
    calls = []

    def fake_run(cmd, *, capture_output, text, cwd):
        assert capture_output is True
        assert text is True
        assert cwd == session_sync.ROOT
        calls.append(cmd)
        if cmd == ["git", "status", "--porcelain"]:
            return DummyResult(stdout="")
        if cmd == ["git", "fetch", "--prune"]:
            return DummyResult(stdout="Fetching origin")
        if cmd == ["git", "pull", "--ff-only"]:
            return DummyResult(stdout="Already up to date.")
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(session_sync.subprocess, "run", fake_run)

    result = session_sync.run_sync()

    assert calls == [
        ["git", "status", "--porcelain"],
        ["git", "fetch", "--prune"],
        ["git", "pull", "--ff-only"],
    ]
    assert result.changed is False
    assert result.dirty is False
    assert "Already up to date" in result.pull_output


def test_run_sync_dirty_repo_requires_override(monkeypatch):
    def fake_run(cmd, *, capture_output, text, cwd):
        assert cwd == session_sync.ROOT
        if cmd == ["git", "status", "--porcelain"]:
            return DummyResult(stdout=" M tools/example.py")
        raise AssertionError

    monkeypatch.setattr(session_sync.subprocess, "run", fake_run)

    with pytest.raises(session_sync.DirtyWorktreeError) as exc:
        session_sync.run_sync()

    assert "Working tree has local changes" in str(exc.value)


def test_run_sync_dirty_repo_allowed(monkeypatch):
    step_iter = iter([
        DummyResult(stdout=" M file.py"),
        DummyResult(stdout="Fetching"),
        DummyResult(stdout="Already up to date"),
    ])

    def fake_run(cmd, *, capture_output, text, cwd):
        assert cwd == session_sync.ROOT
        return next(step_iter)

    monkeypatch.setattr(session_sync.subprocess, "run", fake_run)

    result = session_sync.run_sync(allow_dirty=True)
    assert result.dirty is True


def test_run_sync_detects_updates(monkeypatch):
    step_iter = iter([
        DummyResult(stdout=""),
        DummyResult(stdout="Fetching"),
        DummyResult(stdout="Updating 123..456\n"),
    ])

    def fake_run(cmd, *, capture_output, text, cwd):
        assert cwd == session_sync.ROOT
        return next(step_iter)

    monkeypatch.setattr(session_sync.subprocess, "run", fake_run)

    result = session_sync.run_sync()
    assert result.changed is True


def test_main_reports_failure(monkeypatch, capsys):
    def fake_run_sync(**_):
        raise session_sync.GitCommandError(["fetch", "--prune"], DummyResult(stderr="boom", returncode=1))

    monkeypatch.setattr(session_sync, "run_sync", fake_run_sync)

    exit_code = session_sync.main([])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Session sync failed" in captured.err


def test_main_quiet(monkeypatch, capsys):
    def fake_run_sync(**_):
        return session_sync.SyncResult(changed=False, fetch_output="", pull_output="", dirty=False)

    monkeypatch.setattr(session_sync, "run_sync", fake_run_sync)

    exit_code = session_sync.main(["--quiet"])

    assert exit_code == 0
    out = capsys.readouterr().out.strip()
    assert out == "Session sync succeeded (already up to date)."
