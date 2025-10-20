import json
from pathlib import Path

import pytest

from tools.autonomy import backlog_steward as steward
from tools.autonomy import receipt_utils


@pytest.fixture(autouse=True)
def patch_default_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(steward, "DEFAULT_BACKLOG", tmp_path / "backlog.json")
    monkeypatch.setattr(steward, "DEFAULT_PLANS_DIR", tmp_path / "plans")
    monkeypatch.setattr(steward, "DEFAULT_OUT_DIR", tmp_path / "reports")
    monkeypatch.setattr(receipt_utils, "DEFAULT_PLANS_DIR", tmp_path / "plans")


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_apply_updates(tmp_path: Path):
    backlog = {
        "version": 0,
        "owner": "codex",
        "updated": "2025-01-01T00:00:00Z",
        "items": [
            {
                "id": "ND-001",
                "title": "Example",
                "status": "pending",
                "plan_suggestion": "2025-01-01-example",
            }
        ],
    }
    _write(tmp_path / "backlog.json", backlog)

    plan = {
        "plan_id": "2025-01-01-example",
        "status": "done",
        "steps": [
            {
                "id": "step-1",
                "status": "done",
                "receipts": ["docs/example.md"],
            }
        ],
        "receipts": ["_report/example.json"],
    }
    _write(tmp_path / "plans" / "2025-01-01-example.plan.json", plan)

    exit_code = steward.main(["--apply", "--quiet"])
    assert exit_code == 0

    backlog_path = tmp_path / "backlog.json"
    updated = json.loads(backlog_path.read_text(encoding="utf-8"))
    assert updated["items"] == []
    assert "archive_ref" in updated
    ref_meta = updated["archive_ref"]
    assert ref_meta["path"].endswith("backlog.archive.json")
    archive_path = backlog_path.with_name("backlog.archive.json")
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    assert archive["count"] == 1
    archived_item = archive["items"][0]
    assert archived_item["status"] == "done"
    assert "completed_at" in archived_item
    assert "receipts" not in archived_item
    ref = archived_item["receipts_ref"]
    assert ref["kind"] == "plan"
    assert ref["plan_id"] == "2025-01-01-example"
    assert ref["count"] == 2
    assert "digest" in ref


def test_dry_run(tmp_path: Path, capsys):
    backlog = {
        "version": 0,
        "owner": "codex",
        "updated": "2025-01-01T00:00:00Z",
        "items": [
            {
                "id": "ND-002",
                "title": "Pending",
                "status": "pending",
                "plan_suggestion": "2025-01-02-plan",
            }
        ],
    }
    _write(tmp_path / "backlog.json", backlog)

    plan = {
        "plan_id": "2025-01-02-plan",
        "status": "done",
        "receipts": ["docs/another.md"],
        "steps": [],
    }
    _write(tmp_path / "plans" / "2025-01-02-plan.plan.json", plan)

    exit_code = steward.main(["--dry-run"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "backlog_steward" in out

    untouched = json.loads((tmp_path / "backlog.json").read_text(encoding="utf-8"))
    assert untouched["items"][0]["status"] == "pending"
    assert not (tmp_path / "backlog.archive.json").exists()
