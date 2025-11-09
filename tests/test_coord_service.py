from __future__ import annotations

import json

import pytest

from tools.autonomy.coord.service import CoordinationService, CoordinationServiceError


def _write_json(path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_select_work_returns_first_pending(tmp_path):
    plan_id = "PLAN-123"
    plan = {
        "plan_id": plan_id,
        "steps": [
            {"id": "step-1", "status": "done"},
            {"id": "step-2", "status": "queued"},
        ],
    }
    todo = {
        "items": [
            {"id": "ND-01", "status": "pending", "plan_suggestion": plan_id},
        ]
    }
    _write_json(tmp_path / "_plans" / f"{plan_id}.plan.json", plan)
    _write_json(tmp_path / "_plans" / "next-development.todo.json", todo)

    service = CoordinationService(root=tmp_path)
    item, loaded_plan, step = service.select_work()

    assert item["id"] == "ND-01"
    assert loaded_plan["plan_id"] == plan_id
    assert step["id"] == "step-2"


def test_select_work_raises_when_no_actionable_item(tmp_path):
    todo = {"items": [{"id": "ND-01", "status": "done", "plan_suggestion": "PLAN-1"}]}
    _write_json(tmp_path / "_plans" / "next-development.todo.json", todo)

    service = CoordinationService(root=tmp_path)
    with pytest.raises(CoordinationServiceError):
        service.select_work()


def test_select_step_errors_for_unknown_step(tmp_path):
    plan = {
        "plan_id": "PLAN-2",
        "steps": [{"id": "step-1", "status": "queued"}],
    }
    service = CoordinationService(root=tmp_path)
    with pytest.raises(CoordinationServiceError):
        service.select_step(plan, "missing")
