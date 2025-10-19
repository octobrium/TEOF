import json
from pathlib import Path

import pytest

from tools.autonomy import coordinator_manager as cm


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_main_writes_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan_id = "2025-10-19-test"
    plan_payload = {
        "plan_id": plan_id,
        "summary": "Test plan",
        "systemic_targets": ["S1"],
        "layer_targets": ["L5"],
        "priority": 2,
        "impact_score": 3,
        "steps": [
            {
                "id": "step-1",
                "title": "Do the thing",
                "status": "queued",
                "notes": "",
            }
        ],
    }
    plan_dir = tmp_path / "plans"
    monkeypatch.setattr(cm, "PLANS_DIR", plan_dir)
    _write_json(plan_dir / f"{plan_id}.plan.json", plan_payload)

    manifest_meta = {"agent_id": "codex-4"}
    manifest_file = tmp_path / "manifest.json"
    monkeypatch.setattr(cm, "MANIFEST_FILE", manifest_file)
    _write_json(manifest_file, manifest_meta)

    out_path = tmp_path / "manifest-output.json"
    result = cm.main(["--plan", plan_id, "--step", "step-1", "--out", str(out_path)])
    assert result == 0

    rendered = json.loads(out_path.read_text(encoding="utf-8"))
    assert rendered["manager_agent"] == "codex-4"
    assert rendered["plan"]["id"] == plan_id
    assert rendered["step"]["id"] == "step-1"
    assert rendered["commands"], "expected commands missing"
    assert rendered["expected_receipts"], "expected receipts missing"
    assert "receipt_sha256" in rendered
