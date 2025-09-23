from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.autonomy import auto_loop


@pytest.fixture()
def consent_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    policy = {
        "auto_enabled": True,
        "continuous": True,
        "require_execute": True,
        "allow_apply": True,
        "max_iterations": 0,
    }
    consent = tmp_path / "docs" / "automation" / "autonomy-consent.json"
    consent.parent.mkdir(parents=True, exist_ok=True)
    consent.write_text(json.dumps(policy), encoding="utf-8")

    log_dir = tmp_path / "_report" / "usage" / "autonomy-loop"
    log_dir.mkdir(parents=True, exist_ok=True)

    todo = tmp_path / "_plans" / "next-development.todo.json"
    todo.parent.mkdir(parents=True, exist_ok=True)
    todo.write_text(
        json.dumps(
            {
                "version": 0,
                "owner": "test",
                "updated": "2025-01-01T00:00:00Z",
                "items": [
                    {
                        "id": "ND-001",
                        "title": "done item",
                        "status": "done",
                        "plan_suggestion": "PLAN",
                    }
                ],
                "history": [],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(auto_loop, "ROOT", tmp_path)
    monkeypatch.setattr(auto_loop, "CONSENT_PATH", consent)
    monkeypatch.setattr(auto_loop, "LOG_DIR", log_dir)
    monkeypatch.setattr(auto_loop, "LOG_FILE", log_dir / "auto-loop.log")
    monkeypatch.setattr(auto_loop, "PID_FILE", log_dir / "auto-loop.pid")
    monkeypatch.setattr(auto_loop, "TODO_PATH", todo)
    monkeypatch.setattr(auto_loop.backlog_synth, "synthesise", lambda: {"added": []})
    return tmp_path


def test_run_loop_halts_when_no_pending(consent_policy: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runs = []

    def fake_invoke(*, allow_apply: bool, skip_synth: bool):
        runs.append((allow_apply, skip_synth))
        return 0, {}

    monkeypatch.setattr(auto_loop, "_invoke_next_step", fake_invoke)
    auto_loop.run_loop(
        sleep_seconds=0.0,
        max_cycles=5,
        skip_synth=True,
        watch=False,
        max_idle=1,
        max_runtime=None,
    )
    assert runs == [(True, True)]


def test_background_start_creates_pid(consent_policy: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    launches: list[list[str]] = []

    class Proc:
        pid = 1234

    def fake_popen(cmd, cwd, stdout, stderr, text, start_new_session):
        launches.append(cmd)
        return Proc()

    monkeypatch.setattr(auto_loop.subprocess, "Popen", fake_popen)
    rc = auto_loop.main(["--background", "--sleep", "0", "--max-cycles", "1"])
    assert rc == 0
    assert auto_loop.PID_FILE.read_text(encoding="utf-8") == "1234"
    assert launches
    assert "--watch" not in launches[0]


def test_background_watch_flag(consent_policy: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    launches: list[list[str]] = []

    class Proc:
        pid = 4321

    def fake_popen(cmd, cwd, stdout, stderr, text, start_new_session):
        launches.append(cmd)
        return Proc()

    monkeypatch.setattr(auto_loop.subprocess, "Popen", fake_popen)
    rc = auto_loop.main(["--background", "--sleep", "0", "--watch", "--max-cycles", "1"])
    assert rc == 0
    assert auto_loop.PID_FILE.read_text(encoding="utf-8") == "4321"
    assert launches
    assert "--watch" in launches[0]


def test_status_and_stop(consent_policy: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    auto_loop.PID_FILE.write_text("9999", encoding="utf-8")

    def fake_kill(pid, sig=0):
        raise OSError

    monkeypatch.setattr(auto_loop.os, "kill", fake_kill)
    rc = auto_loop.main(["--status"])
    assert rc == 0
    rc = auto_loop.main(["--stop"])
    assert rc == 0


def test_watch_mode_retries(consent_policy: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [0, 1]

    def fake_invoke(*, allow_apply: bool, skip_synth: bool):
        result = responses.pop(0)
        if result:
            return 1, {"runs": [{"id": "ND-999", "status": "done"}]}
        return 0, {}

    monkeypatch.setattr(auto_loop, "_invoke_next_step", fake_invoke)
    auto_loop.run_loop(
        sleep_seconds=0.0,
        max_cycles=1,
        skip_synth=False,
        watch=True,
        max_idle=2,
        max_runtime=None,
    )
    assert not responses
    todo = json.loads(auto_loop.TODO_PATH.read_text(encoding="utf-8"))
    assert any(item.get("status") == "pending" for item in todo.get("items", []))
