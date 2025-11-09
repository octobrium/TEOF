from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from teof.commands import plan_scope as plan_scope_mod


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
    monkeypatch.setattr(plan_scope_mod, "ROOT", root, raising=False)
    monkeypatch.setattr(plan_scope_mod, "PLANS_DIR", root / "_plans", raising=False)
    monkeypatch.setattr(plan_scope_mod, "TASKS_PATH", root / "agents" / "tasks" / "tasks.json", raising=False)
    monkeypatch.setattr(plan_scope_mod, "CLAIMS_DIR", root / "_bus" / "claims", raising=False)
    monkeypatch.setattr(plan_scope_mod, "ASSIGNMENTS_DIR", root / "_bus" / "assignments", raising=False)
    monkeypatch.setattr(plan_scope_mod, "MESSAGES_DIR", root / "_bus" / "messages", raising=False)
    monkeypatch.setattr(plan_scope_mod, "RECEIPT_DIR", root / "_report" / "usage" / "plan-scope", raising=False)


def _run_plan_scope(**kwargs: object) -> int:
    defaults: dict[str, object] = {
        "plan": "demo-plan",
        "format": "table",
        "manifest": None,
        "receipt_dir": None,
        "no_receipt": False,
    }
    defaults.update(kwargs)
    args = Namespace(**defaults)
    return plan_scope_mod.run(args)


def test_plan_scope_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _seed_plan(tmp_path)
    _seed_tasks(tmp_path)
    _patch_plan_scope(tmp_path, monkeypatch)

    exit_code = _run_plan_scope(format="json")
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["plan_id"] == "demo-plan"
    paths = {entry["path"]: entry for entry in payload["files"]}
    assert "README.md" in paths
    assert "_bus/claims/QUEUE-001.json" in paths
    assert paths["_bus/messages/QUEUE-001.jsonl"]["exists"] is True
    assert "receipt" in payload
    receipt_path = tmp_path / payload["receipt"]
    assert receipt_path.exists()


def test_plan_scope_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _seed_plan(tmp_path)
    _seed_tasks(tmp_path)
    _patch_plan_scope(tmp_path, monkeypatch)

    manifest_path = tmp_path / "_plan_scope" / "demo.json"
    exit_code = _run_plan_scope(manifest=str(manifest_path.relative_to(tmp_path)))
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "wrote manifest" in output
    assert "receipt → " in output
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["plan_id"] == "demo-plan"
    assert manifest["files"]
    receipt_dir = tmp_path / "_report" / "usage" / "plan-scope"
    receipts = [path for path in receipt_dir.glob("plan-scope-*.json")]
    assert receipts, "expected plan_scope receipt to be recorded"


def test_plan_scope_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _seed_plan(tmp_path)
    _seed_tasks(tmp_path)
    _patch_plan_scope(tmp_path, monkeypatch)

    manifest_rel = "_plan_scope/manifests/demo.json"
    exit_code = _run_plan_scope(manifest=manifest_rel, format="json")
    assert exit_code == 0
    captured = capsys.readouterr().out
    marker = '{\n  "plan_id"'
    start = captured.rfind(marker)
    assert start != -1
    output = json.loads(captured[start:])
    assert output["plan_id"] == "demo-plan"

    receipt_dir = tmp_path / "_report" / "usage" / "plan-scope"
    receipts = sorted(receipt_dir.glob("plan-scope-demo-plan-*.json"))
    assert len(receipts) == 1
    receipt_payload = json.loads(receipts[0].read_text(encoding="utf-8"))
    assert receipt_payload["plan_id"] == "demo-plan"
    assert receipt_payload["file_count"] == len(output["files"])
    assert receipt_payload["manifest"] == manifest_rel
    pointer = json.loads((receipt_dir / "latest.json").read_text(encoding="utf-8"))
    assert pointer["plan_id"] == "demo-plan"
    assert pointer["receipt"] == f"_report/usage/plan-scope/{receipts[0].name}"


def test_plan_scope_no_receipt_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _seed_plan(tmp_path)
    _seed_tasks(tmp_path)
    _patch_plan_scope(tmp_path, monkeypatch)

    exit_code = _run_plan_scope(format="json", no_receipt=True)
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["plan_id"] == "demo-plan"
    assert "receipt" not in payload
    receipt_dir = tmp_path / "_report" / "usage" / "plan-scope"
    assert not receipt_dir.exists()
