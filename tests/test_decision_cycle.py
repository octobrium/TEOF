from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.autonomy import decision_cycle


@pytest.fixture()
def decision_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    decision_dir = tmp_path / "memory" / "decisions"
    decision_dir.mkdir(parents=True)
    decision_path = decision_dir / "decision-demo.json"
    decision_path.write_text(
        json.dumps(
            {
                "captured_at": "2025-09-23T22:55:00Z",
                "title": "Launch pilot",
                "objective": "Maximise revenue",
                "constraints": ["budget <= 5k"],
                "success_metric": "MRR increase",
                "references": ["docs/vision/impact-ledger.md"],
                "plan_id": "2025-09-23-decision-loop",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(decision_cycle, "ROOT", tmp_path)
    monkeypatch.setattr(decision_cycle, "DECISION_DIR", decision_dir)
    monkeypatch.setattr(decision_cycle, "OUTPUT_DIR", tmp_path / "_report" / "usage" / "decision-loop")
    return decision_path


def test_decision_cycle_writes_payload(decision_record: Path) -> None:
    rc = decision_cycle.main([
        "decision-demo.json",
        "--diff-limit",
        "150",
        "--test",
        "pytest",
    ])
    assert rc == 0
    outputs = list(decision_cycle.OUTPUT_DIR.glob("cycle-*.json"))
    assert outputs
    payload = json.loads(outputs[0].read_text(encoding="utf-8"))
    assert payload["decision"]["title"] == "Launch pilot"
    assert "Guardrails" in payload["prompts"]["proposal"]
    assert "diff limit" in payload["prompts"]["critique"].lower()


def test_decision_cycle_dry_run(decision_record: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = decision_cycle.main(["decision-demo.json", "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Launch pilot" in out
