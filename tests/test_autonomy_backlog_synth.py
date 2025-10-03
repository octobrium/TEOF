import json
from importlib import reload
from pathlib import Path

import pytest

from tools.autonomy import backlog_synth


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sample_advisories() -> dict:
    return {
        "generated_at": "2025-10-03T02:50:00Z",
        "source_receipt": "_report/fractal/conformance/latest.json",
        "advisories": [
            {
                "id": "ADV-test-1",
                "claim": "Plan foo is missing metadata",
                "layer": "L5",
                "systemic_scale": 5,
                "targets": ["_plans/foo.plan.json"],
                "source_receipt": "_report/fractal/conformance/latest.json",
                "evidence": {"receipts": ["_report/fractal/conformance/latest.json"]},
            },
            {
                "id": "ADV-test-2",
                "claim": "Memory entry needs systemic scale",
                "layer": "L4",
                "targets": ["memory/log.jsonl#99"],
                "source_receipt": "_report/fractal/conformance/latest.json",
                "evidence": {"receipts": ["_report/fractal/conformance/latest.json"]},
            },
        ],
    }


@pytest.fixture
def temp_repo(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    todo_path = repo_root / "_plans" / "next-development.todo.json"
    policy_path = repo_root / "docs" / "automation" / "backlog-policy.json"
    advisory_path = repo_root / "_report" / "fractal" / "advisories" / "latest.json"
    health_path = repo_root / "_report" / "health" / "health-20251003T000000Z.json"

    _write_json(todo_path, {"items": []})
    _write_json(policy_path, {
        "version": 0,
        "rules": [
            {
                "id": "FRACTAL-ADVISORY",
                "description": "Surface advisories",
                "conditions": {"advisories": str(advisory_path.relative_to(repo_root))},
                "plan_suggestion": "2025-09-29-autonomous-backlog"
            }
        ]
    })
    _write_json(advisory_path, _sample_advisories())
    _write_json(health_path, {"generated_at": "2025-10-03T02:40:00Z"})

    reload(backlog_synth)
    monkeypatch.setattr(backlog_synth, "ROOT", repo_root)
    monkeypatch.setattr(backlog_synth, "TODO_PATH", todo_path)
    monkeypatch.setattr(backlog_synth, "POLICY_PATH", policy_path)
    monkeypatch.setattr(backlog_synth, "RECEIPT_DIR", repo_root / "_report" / "autonomy" / "backlog-synth")
    monkeypatch.setattr(backlog_synth.health_sensors, "emit_health_report", lambda: health_path)

    return repo_root, todo_path, policy_path, advisory_path


def test_advisory_rule_adds_backlog_items(temp_repo):
    repo_root, todo_path, policy_path, advisory_path = temp_repo

    result = backlog_synth.synthesise(todo_path=todo_path, policy_path=policy_path)

    added_ids = {item["id"] for item in result["added"]}
    assert added_ids == {"ADV-test-1", "ADV-test-2"}
    assert "receipt_path" in result

    todo_payload = json.loads(todo_path.read_text(encoding="utf-8"))
    todo_ids = {item["id"] for item in todo_payload["items"]}
    assert added_ids == todo_ids

    receipt_path = repo_root / result["receipt_path"]
    assert receipt_path.exists()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert {entry["id"] for entry in receipt["added"]} == added_ids
    assert receipt["advisories"][0]["path"] == str(advisory_path.relative_to(repo_root))


def test_advisory_rule_is_idempotent(temp_repo):
    repo_root, todo_path, policy_path, _ = temp_repo

    first = backlog_synth.synthesise(todo_path=todo_path, policy_path=policy_path)
    assert first["added"]

    second = backlog_synth.synthesise(todo_path=todo_path, policy_path=policy_path)
    assert second["added"] == []
    assert "receipt_path" not in second

    todo_payload = json.loads(todo_path.read_text(encoding="utf-8"))
    assert len(todo_payload["items"]) == len(first["added"])
