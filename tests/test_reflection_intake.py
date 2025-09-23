from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.autonomy import reflection_intake


@pytest.fixture()
def reflection_root(tmp_path: Path) -> Path:
    (tmp_path / "memory").mkdir()
    (tmp_path / "_report" / "usage").mkdir(parents=True)
    return tmp_path


def test_reflection_intake_writes_record(reflection_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    args = [
        "--title",
        "Morning insight",
        "--layer",
        "L0",
        "--summary",
        "Observed a recurring pattern in decision making.",
        "--signals",
        "Journaling notes from the week",
        "--actions",
        "Schedule weekly review",
        "--tag",
        "mindset",
        "--plan-suggestion",
        "2025-09-23-autonomy-roadmap",
        "--backlog-out",
        str(reflection_root / "_report" / "usage" / "reflection-intake" / "candidate.json"),
        "--emit-backlog",
        "--root",
        str(reflection_root),
    ]

    rc = reflection_intake.main(args)
    assert rc == 0

    reflections_dir = reflection_root / "memory" / "reflections"
    files = list(reflections_dir.glob("reflection-*.json"))
    assert files, "reflection file missing"
    payload = json.loads(files[-1].read_text(encoding="utf-8"))
    assert payload["title"] == "Morning insight"
    assert payload["layers"] == ["L0"]
    assert payload["plan_suggestion"] == "2025-09-23-autonomy-roadmap"

    backlog_out = reflection_root / "_report" / "usage" / "reflection-intake" / "candidate.json"
    assert backlog_out.exists()
    backlog_payload = json.loads(backlog_out.read_text(encoding="utf-8"))
    assert backlog_payload["title"] == "Morning insight"
    assert backlog_payload["plan_suggestion"] == "2025-09-23-autonomy-roadmap"
    assert backlog_payload["layer"] == "L0"

    captured = capsys.readouterr()
    assert "reflection: wrote" in captured.out
    assert "reflection: backlog suggestion" in captured.out


def test_reflection_intake_dry_run(reflection_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    args = [
        "--title",
        "Dry run",
        "--layer",
        "L1",
        "--summary",
        "Testing dry-run output",
        "--dry-run",
        "--emit-backlog",
        "--root",
        str(reflection_root),
    ]

    rc = reflection_intake.main(args)
    assert rc == 0
    reflections_dir = reflection_root / "memory" / "reflections"
    assert not reflections_dir.exists()
    captured = capsys.readouterr()
    assert "Testing dry-run output" in captured.out
