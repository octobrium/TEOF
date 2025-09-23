from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.autonomy import decision_intake


def test_write_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    decisions_dir = tmp_path / "memory" / "decisions"
    monkeypatch.setattr(decision_intake, "DECISION_DIR", decisions_dir)

    record = {
        "captured_at": "2025-09-23T22:50:00Z",
        "title": "Decide",
        "objective": "Grow",
        "constraints": ["budget"],
        "success_metric": "ROI",
        "references": ["memory/reflections/x.json"],
        "tags": ["impact"],
        "plan_id": "2025-09-23-decision-loop",
    }

    path = decision_intake.write_record(record, dry_run=False)
    assert path is not None
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["title"] == "Decide"
    assert data["objective"] == "Grow"


def test_main_dry_run(capsys: pytest.CaptureFixture[str]) -> None:
    args = [
        "--title",
        "Demo",
        "--objective",
        "Test",
        "--dry-run",
    ]
    rc = decision_intake.main(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Demo" in out
