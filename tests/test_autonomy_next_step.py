from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.autonomy import next_step


@pytest.fixture()
def tmp_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    todo = tmp_path / "_plans" / "next-development.todo.json"
    todo.parent.mkdir(parents=True, exist_ok=True)
    todo.write_text(
        json.dumps(
            {
                "prerequisites": {
                    "min_overall_trust": 0.7,
                    "require_no_attention_feeds": True,
                },
                "items": [
                    {
                        "id": "ND-TEST",
                        "title": "Test item",
                        "status": "pending",
                        "plan_suggestion": "PLAN-TEST",
                        "notes": "demo",
                    }
                ],
                "history": [],
            }
        ),
        encoding="utf-8",
    )

    authenticity = tmp_path / "_report" / "usage" / "external-authenticity.json"
    authenticity.parent.mkdir(parents=True, exist_ok=True)
    authenticity.write_text(
        json.dumps(
            {
                "overall_avg_trust": 0.9,
                "attention_feeds": [],
            }
        ),
        encoding="utf-8",
    )

    status = tmp_path / "_report" / "planner" / "validate" / "summary-latest.json"
    status.parent.mkdir(parents=True, exist_ok=True)
    status.write_text(json.dumps({"exit_code": 0}), encoding="utf-8")

    monkeypatch.setattr(next_step, "TODO_PATH", todo)
    monkeypatch.setattr(next_step, "AUTH_JSON", authenticity)
    monkeypatch.setattr(next_step, "STATUS_PATH", status)
    monkeypatch.setattr(next_step, "ROOT", tmp_path)
    return tmp_path


def test_execute_action_dry_run(tmp_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    reports: list[Path] = []

    def fake_action(*, root: Path, dry_run: bool) -> dict:
        report = root / "_report" / "usage" / "autonomy-actions" / "fake.json"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps({"dry_run": dry_run}), encoding="utf-8")
        reports.append(report)
        return {"report_path": report, "result": {"dry_run": dry_run}}

    monkeypatch.setattr(next_step.actions, "resolve", lambda plan_id: fake_action)

    rc = next_step.main(["--claim", "--execute", "--skip-synth"])
    assert rc == 0

    captured = json.loads(capsys.readouterr().out)
    assert captured["action"]["result"]["dry_run"] is True
    assert reports[0].exists()


def test_execute_action_apply(tmp_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    calls: list[bool] = []

    def fake_action(*, root: Path, dry_run: bool) -> dict:
        calls.append(dry_run)
        return {"result": {"dry_run": dry_run}}

    monkeypatch.setattr(next_step.actions, "resolve", lambda plan_id: fake_action)

    rc = next_step.main(["--claim", "--execute", "--apply", "--skip-synth"])
    assert rc == 0
    assert calls == [False]
    captured = json.loads(capsys.readouterr().out)
    assert captured["action"]["result"]["dry_run"] is False
