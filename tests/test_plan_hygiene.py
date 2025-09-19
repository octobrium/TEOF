import json
from pathlib import Path

import pytest

from tools.maintenance import plan_hygiene


def write_plan(path: Path, *, status: str, step_status: str, checkpoint_status: str) -> None:
    data = {
        "plan_id": "PLAN-TEST",
        "status": status,
        "steps": [
            {
                "id": "S1",
                "status": step_status,
            }
        ],
        "checkpoint": {
            "status": checkpoint_status,
        },
    }
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


@pytest.fixture
def plans_root(tmp_path: Path) -> Path:
    plans_dir = tmp_path / "_plans"
    plans_dir.mkdir(parents=True)
    return tmp_path


def test_plan_hygiene_detects_and_fixes_known_synonyms(plans_root: Path, capsys: pytest.CaptureFixture) -> None:
    plan_path = plans_root / "_plans" / "demo.plan.json"
    write_plan(
        plan_path,
        status="in-progress",
        step_status="Completed",
        checkpoint_status="Pending",
    )

    rc = plan_hygiene.run([plan_path.relative_to(plans_root)], apply=False, root=plans_root)
    assert rc == 1
    out = capsys.readouterr().out
    assert "FIXABLE" in out
    assert "in-progress" in out

    rc = plan_hygiene.run([plan_path.relative_to(plans_root)], apply=True, root=plans_root)
    assert rc == 0
    normalized = json.loads(plan_path.read_text(encoding="utf-8"))
    assert normalized["status"] == "in_progress"
    assert normalized["steps"][0]["status"] == "done"
    assert normalized["checkpoint"]["status"] == "pending"


def test_plan_hygiene_flags_unknown_values(plans_root: Path, capsys: pytest.CaptureFixture) -> None:
    plan_path = plans_root / "_plans" / "bad.plan.json"
    write_plan(plan_path, status="weird", step_status="queued", checkpoint_status="pending")

    rc = plan_hygiene.run([plan_path.relative_to(plans_root)], apply=True, root=plans_root)
    out = capsys.readouterr().out
    assert rc == 2
    assert "ERROR" in out
    assert "weird" in out
    assert json.loads(plan_path.read_text(encoding="utf-8"))["status"] == "weird"


def test_plan_hygiene_flags_duplicate_receipts(plans_root: Path, capsys: pytest.CaptureFixture) -> None:
    plan_path = plans_root / "_plans" / "dup.plan.json"
    data = {
        "plan_id": "PLAN-DUP",
        "status": "queued",
        "steps": [
            {
                "id": "S1",
                "status": "queued",
                "receipts": ["_report/sample.json", "_report/sample.json"],
            }
        ],
        "checkpoint": {"status": "pending"},
        "receipts": ["_report/root.json", "_report/root.json"],
    }
    plan_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    rc = plan_hygiene.run([plan_path.relative_to(plans_root)], apply=False, root=plans_root)
    out = capsys.readouterr().out
    assert rc == 2
    assert "duplicate" in out
    assert "receipts[1]" in out
    assert "steps[0].receipts[1]" in out
