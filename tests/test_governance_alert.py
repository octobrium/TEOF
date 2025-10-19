import json
from pathlib import Path

import pytest

from tools.autonomy import governance_alert


@pytest.fixture()
def temp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path
    (root / "docs").mkdir()
    (root / "governance").mkdir()
    monkeypatch.setattr(governance_alert, "ROOT", root)
    return root


def test_emit_alert_detects_changes(temp_root: Path) -> None:
    target = temp_root / "docs" / "workflow.md"
    target.write_text("v1", encoding="utf-8")
    out_dir = temp_root / "alerts"
    state_path = temp_root / "state.json"

    triggered, alert_path = governance_alert.emit_alert(
        out_dir=out_dir,
        state_path=state_path,
        targets=[target],
    )
    assert triggered is False
    assert alert_path is None

    target.write_text("v2", encoding="utf-8")

    triggered, alert_path = governance_alert.emit_alert(
        out_dir=out_dir,
        state_path=state_path,
        targets=[target],
    )
    assert triggered is True
    assert alert_path is not None
    payload = json.loads(alert_path.read_text(encoding="utf-8"))
    assert payload["changed"][0]["path"] == "docs/workflow.md"

    latest = (out_dir / "latest.json").read_text(encoding="utf-8")
    assert "docs/workflow.md" in latest
