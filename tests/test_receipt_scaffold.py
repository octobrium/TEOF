import json
from pathlib import Path

import pytest

from tools.receipts import scaffold as receipt_scaffold


@pytest.fixture(autouse=True)
def patch_receipt_roots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    report_root = tmp_path / "_report" / "agent"
    monkeypatch.setattr(receipt_scaffold, "ROOT", tmp_path)
    monkeypatch.setattr(receipt_scaffold, "REPORT_ROOT", report_root)
    yield


def test_scaffold_plan_creates_defaults(tmp_path: Path):
    result = receipt_scaffold.scaffold_plan("2025-09-21-demo", agent="codex-3", include_design=True)
    assert result.created
    target = tmp_path / "_report" / "agent" / "codex-3" / "2025-09-21-demo"
    assert (target / "notes.md").exists()
    actions = json.loads((target / "actions.json").read_text(encoding="utf-8"))
    assert actions["plan_id"] == "2025-09-21-demo"
    assert (target / "design.md").exists()


def test_scaffold_plan_idempotent(tmp_path: Path):
    receipt_scaffold.scaffold_plan("2025-09-21-demo", agent="codex-3")
    second = receipt_scaffold.scaffold_plan("2025-09-21-demo", agent="codex-3")
    assert second.created == []


def test_scaffold_claim_includes_metadata(tmp_path: Path):
    result = receipt_scaffold.scaffold_claim(
        task_id="QUEUE-500",
        agent="codex-9",
        plan_id="2025-09-25-helpers",
        branch="agent/codex-9/queue-500",
    )
    assert result.created
    target = tmp_path / "_report" / "agent" / "codex-9" / "2025-09-25-helpers"
    meta = json.loads((target / "claim.json").read_text(encoding="utf-8"))
    assert meta["task_id"] == "QUEUE-500"
    assert meta["branch"] == "agent/codex-9/queue-500"


def test_format_created_relativizes_paths(tmp_path: Path):
    path = tmp_path / "_report" / "agent" / "codex-1" / "demo" / "notes.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("demo", encoding="utf-8")
    message = receipt_scaffold.format_created([path])
    assert "_report/agent/codex-1/demo/notes.md" in message
