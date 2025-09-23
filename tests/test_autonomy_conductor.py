from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.autonomy import conductor, next_step


@pytest.fixture()
def conductor_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "docs" / "automation").mkdir(parents=True, exist_ok=True)
    consent = tmp_path / "docs" / "automation" / "autonomy-consent.json"
    consent.write_text(
        json.dumps(
            {
                "auto_enabled": True,
                "continuous": True,
                "require_execute": True,
                "allow_apply": True,
                "max_iterations": 0,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    todo = {
        "version": 0,
        "owner": "test",
        "updated": "2025-01-01T00:00:00Z",
        "items": [
            {
                "id": "ND-101",
                "title": "Test autonomy task",
                "status": "pending",
                "plan_suggestion": "PLAN-TEST",
                "notes": "demo task",
            }
        ],
        "history": [],
    }
    todo_path = tmp_path / "_plans" / "next-development.todo.json"
    todo_path.parent.mkdir(parents=True, exist_ok=True)
    todo_path.write_text(json.dumps(todo, indent=2) + "\n", encoding="utf-8")

    monkeypatch.setattr(next_step, "ROOT", tmp_path)
    monkeypatch.setattr(next_step, "TODO_PATH", todo_path)
    monkeypatch.setattr(next_step, "AUTH_JSON", tmp_path / "auth.json")
    (tmp_path / "auth.json").write_text(
        json.dumps({"overall_avg_trust": 0.9, "attention_feeds": []}) + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(next_step, "STATUS_PATH", tmp_path / "status.json")
    (tmp_path / "status.json").write_text(json.dumps({"status": "ok"}) + "\n", encoding="utf-8")

    monkeypatch.setattr(conductor, "ROOT", tmp_path)
    monkeypatch.setattr(conductor, "OUTPUT_DIR", tmp_path / "_report" / "usage" / "autonomy-conductor")
    monkeypatch.setattr(conductor, "consent_policy", None, raising=False)


def test_conductor_dry_run_generates_prompt(conductor_repo: None) -> None:
    rc = conductor.main(["--diff-limit", "123", "--receipts-dir", "_report/custom", "--dry-run"])
    assert rc == 0
    output_dir = conductor.OUTPUT_DIR
    receipts = sorted(output_dir.glob("conductor-*.json"))
    assert receipts
    payload = json.loads(receipts[-1].read_text(encoding="utf-8"))
    assert payload["task"]["id"] == "ND-101"
    assert "Diff limit: 123" in payload["prompt"]
    todo = json.loads((next_step.TODO_PATH).read_text(encoding="utf-8"))
    assert any(item.get("status") == "pending" for item in todo["items"])
