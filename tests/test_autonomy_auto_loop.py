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
    monkeypatch.setattr(auto_loop.session_guard, "resolve_agent_id", lambda explicit=None: "codex-test")
    monkeypatch.setattr(auto_loop.session_guard, "ensure_recent_session", lambda *a, **k: None)

    base_report = auto_loop.parallel_guard.ParallelReport(
        agent_id="codex-test",
        severity="none",
        generated_at="2025-10-05T00:00:00Z",
        config={},
    )
    base_report.requirements = {
        "session_boot": False,
        "plan_claim": False,
        "post_run_scan": False,
    }
    monkeypatch.setattr(
        auto_loop.parallel_guard,
        "detect_parallel_state",
        lambda agent_id, *, now=None: base_report,
    )
    monkeypatch.setattr(
        auto_loop.parallel_guard,
        "write_parallel_receipt",
        lambda agent_id, report: log_dir / "parallel.json",
    )
    monkeypatch.setattr(auto_loop.parallel_guard, "agent_has_active_claim", lambda agent_id, report=None: True)
    return tmp_path


def test_run_loop_halts_when_no_pending(consent_policy: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runs = []

    def fake_invoke(*, allow_apply: bool, skip_synth: bool, agent_id: str | None):
        runs.append((allow_apply, skip_synth, agent_id))
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
    assert runs == [(True, True, None)]


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

    def fake_invoke(*, allow_apply: bool, skip_synth: bool, agent_id: str | None):
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


def test_parallel_guard_halts_loop(consent_policy: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    receipts: list[dict[str, object]] = []

    def detect(agent_id, *, now=None):
        report = auto_loop.parallel_guard.ParallelReport(
            agent_id=agent_id,
            severity="hard",
            generated_at="2025-10-05T01:02:03Z",
            config={},
        )
        report.requirements = {
            "session_boot": True,
            "plan_claim": True,
            "post_run_scan": True,
        }
        report.self_active_claims = []
        return report

    monkeypatch.setattr(auto_loop.parallel_guard, "detect_parallel_state", detect)
    monkeypatch.setattr(auto_loop.parallel_guard, "write_parallel_receipt", lambda agent_id, report: auto_loop.LOG_DIR / "parallel-halt.json")
    monkeypatch.setattr(auto_loop.parallel_guard, "agent_has_active_claim", lambda agent_id, report=None: False)

    def record_event(report: auto_loop.parallel_guard.ParallelReport, *, reason: str, agent_id: str | None):
        payload = report.to_payload()
        payload["reason"] = reason
        receipts.append(payload)
        return auto_loop.LOG_DIR / "parallel-halt.json"

    monkeypatch.setattr(auto_loop, "_record_parallel_event", record_event)
    monkeypatch.setattr(auto_loop, "_invoke_next_step", lambda **_: pytest.fail("should not invoke next_step"))

    auto_loop.run_loop(
        sleep_seconds=0.0,
        max_cycles=1,
        skip_synth=True,
        watch=False,
        max_idle=0,
        max_runtime=None,
        agent_id="codex-test",
    )

    assert receipts and receipts[0]["severity"] == "hard"


def test_main_writes_objectives_status(consent_policy: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run_loop(**kwargs: object) -> None:
        return None

    called: dict[str, float] = {}

    def fake_compute_status(window_days: float) -> dict[str, object]:
        called["window"] = window_days
        return {"ok": True}

    status_path = consent_policy / "_report" / "usage" / "objectives-status.json"

    monkeypatch.setattr(auto_loop, "run_loop", fake_run_loop)
    monkeypatch.setattr(auto_loop.objectives_status, "compute_status", fake_compute_status)
    monkeypatch.setattr(auto_loop, "OBJECTIVES_STATUS_PATH", status_path)

    rc = auto_loop.main([])
    assert rc == 0
    assert called["window"] == 7.0
    assert json.loads(status_path.read_text(encoding="utf-8")) == {"ok": True}
