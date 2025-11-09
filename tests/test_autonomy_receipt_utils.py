import json
from pathlib import Path

import pytest

from tools.autonomy import receipt_utils


@pytest.fixture()
def plans_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path
    plans = root / "plans"
    guards = root / "_report" / "ethics" / "guards"
    plans.mkdir(parents=True, exist_ok=True)
    guards.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(receipt_utils, "ROOT", root)
    monkeypatch.setattr(receipt_utils, "DEFAULT_PLANS_DIR", plans)
    monkeypatch.setattr(receipt_utils, "GUARDS_DIR", guards)
    return plans


def test_collect_plan_receipts(plans_dir: Path) -> None:
    payload = {
        "status": "done",
        "receipts": ["docs/root.md"],
        "steps": [
            {"id": "S1", "status": "done", "receipts": ["_report/step.json", "docs/root.md"]},
            {"id": "S2", "status": "done"},
        ],
    }
    (plans_dir / "2025-01-10-example.plan.json").write_text(json.dumps(payload), encoding="utf-8")
    receipts = receipt_utils.collect_plan_receipts("2025-01-10-example")
    assert receipts == ["docs/root.md", "_report/step.json"]


def test_resolve_item_receipts_with_ref(plans_dir: Path) -> None:
    payload = {
        "status": "done",
        "receipts": ["docs/root.md"],
    }
    (plans_dir / "2025-01-11-example.plan.json").write_text(json.dumps(payload), encoding="utf-8")
    item = {
        "id": "ND-123",
        "receipts_ref": {"kind": "plan", "plan_id": "2025-01-11-example"},
    }
    receipts = receipt_utils.resolve_item_receipts(item)
    assert receipts == ["docs/root.md"]


def test_resolve_item_receipts_includes_guard(plans_dir: Path) -> None:
    guards_root = receipt_utils.GUARDS_DIR / "2025-11-09"
    guards_root.mkdir(parents=True, exist_ok=True)
    guard = guards_root / "nd-900-ethics.json"
    guard.write_text("{}", encoding="utf-8")
    item = {"id": "ND-900"}
    receipts = receipt_utils.resolve_item_receipts(item)
    assert receipts == ["_report/ethics/guards/2025-11-09/nd-900-ethics.json"]
