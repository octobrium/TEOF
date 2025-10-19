import json
from pathlib import Path

import pytest

from tools.autonomy import coordinator_loop as loop


@pytest.fixture(autouse=True)
def patch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(loop, "ROOT", tmp_path)
    monkeypatch.setattr(loop, "TODO_PATH", tmp_path / "_plans" / "next-development.todo.json")


def _write_plan(tmp_path: Path, plan_id: str) -> None:
    plan = {
        "plan_id": plan_id,
        "summary": "Plan summary",
        "systemic_targets": ["S1"],
        "layer_targets": ["L5"],
        "steps": [
            {"id": "step-1", "title": "First", "status": "done"},
            {"id": "step-2", "title": "Second", "status": "queued"},
        ],
    }
    plan_path = tmp_path / "_plans"
    plan_path.mkdir(parents=True, exist_ok=True)
    (plan_path / f"{plan_id}.plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_todo(tmp_path: Path, plan_id: str) -> None:
    todo = {
        "items": [
            {
                "id": "ND-999",
                "status": "pending",
                "plan_suggestion": plan_id,
            }
        ]
    }
    todo_path = tmp_path / "_plans"
    todo_path.mkdir(parents=True, exist_ok=True)
    (todo_path / "next-development.todo.json").write_text(json.dumps(todo, ensure_ascii=False, indent=2), encoding="utf-8")


def test_loop_invokes_orchestrator(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    plan_id = "2025-10-07-plan"
    _write_plan(tmp_path, plan_id)
    _write_todo(tmp_path, plan_id)

    captured = {}

    def fake_main(args):
        captured["args"] = args
        return 0

    monkeypatch.setattr(loop.coordinator_orchestrator, "main", fake_main)

    exit_code = loop.main(["--iterations", "1", "--manager-agent", "codex-4", "--worker-agent", "codex-4"])
    assert exit_code == 0
    assert captured["args"][1] == plan_id
    assert "--task-id" in captured["args"]


def test_loop_dry_run(tmp_path: Path, capsys):
    plan_id = "2025-10-08-plan"
    _write_plan(tmp_path, plan_id)
    _write_todo(tmp_path, plan_id)

    exit_code = loop.main(["--dry-run"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "selected" in out
