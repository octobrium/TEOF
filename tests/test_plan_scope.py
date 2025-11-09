from __future__ import annotations

import json
from pathlib import Path

import pytest

import teof.bootloader as bootloader


def _seed_plan(root: Path) -> None:
    plans_dir = root / "_plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    receipts_dir = root / "docs"
    receipts_dir.mkdir(parents=True, exist_ok=True)
    (receipts_dir / "usage").mkdir(exist_ok=True, parents=True)
    (receipts_dir / "usage" / "chronicle.md").write_text("# chronicle\n", encoding="utf-8")
    (root / "README.md").write_text("readme\n", encoding="utf-8")

    plan = {
        "plan_id": "demo-plan",
        "summary": "Demo",
        "steps": [
            {
                "id": "S1",
                "title": "Step",
                "status": "done",
                "receipts": ["docs/usage/chronicle.md"],
            }
        ],
        "receipts": ["README.md"],
    }
    (plans_dir / "demo-plan.plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


def _seed_tasks(root: Path) -> None:
    tasks_dir = root / "agents" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    tasks_payload = {
        "version": 1,
        "tasks": [
            {"id": "QUEUE-001", "plan_id": "demo-plan", "title": "Demo task"},
            {"id": "QUEUE-002", "plan_id": "other-plan", "title": "Other"},
        ],
    }
    (tasks_dir / "tasks.json").write_text(json.dumps(tasks_payload), encoding="utf-8")
    claim_dir = root / "_bus" / "claims"
    assign_dir = root / "_bus" / "assignments"
    msg_dir = root / "_bus" / "messages"
    claim_dir.mkdir(parents=True, exist_ok=True)
    assign_dir.mkdir(parents=True, exist_ok=True)
    msg_dir.mkdir(parents=True, exist_ok=True)
    (claim_dir / "QUEUE-001.json").write_text("{}", encoding="utf-8")
    (assign_dir / "QUEUE-001.json").write_text("{}", encoding="utf-8")
    (msg_dir / "QUEUE-001.jsonl").write_text("", encoding="utf-8")


def _patch_plan_scope(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from teof.commands import plan_scope as plan_scope_mod

    monkeypatch.setattr(plan_scope_mod, "ROOT", root, raising=False)
    monkeypatch.setattr(plan_scope_mod, "PLANS_DIR", root / "_plans", raising=False)
    monkeypatch.setattr(plan_scope_mod, "TASKS_PATH", root / "agents" / "tasks" / "tasks.json", raising=False)
    monkeypatch.setattr(plan_scope_mod, "CLAIMS_DIR", root / "_bus" / "claims", raising=False)
    monkeypatch.setattr(plan_scope_mod, "ASSIGNMENTS_DIR", root / "_bus" / "assignments", raising=False)
    monkeypatch.setattr(plan_scope_mod, "MESSAGES_DIR", root / "_bus" / "messages", raising=False)


def test_plan_scope_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _seed_plan(tmp_path)
    _seed_tasks(tmp_path)
    _patch_plan_scope(tmp_path, monkeypatch)
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)

    exit_code = bootloader.main(["plan_scope", "--plan", "demo-plan", "--format", "json"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["plan_id"] == "demo-plan"
    paths = {entry["path"]: entry for entry in payload["files"]}
    assert "README.md" in paths
    assert "_bus/claims/QUEUE-001.json" in paths
    assert paths["_bus/messages/QUEUE-001.jsonl"]["exists"] is True


def test_plan_scope_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _seed_plan(tmp_path)
    _seed_tasks(tmp_path)
    _patch_plan_scope(tmp_path, monkeypatch)
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)

    manifest_path = tmp_path / "_plan_scope" / "demo.json"
    exit_code = bootloader.main(
        ["plan_scope", "--plan", "demo-plan", "--manifest", str(manifest_path.relative_to(tmp_path))]
    )
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "wrote manifest" in output
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["plan_id"] == "demo-plan"
    assert manifest["files"]
