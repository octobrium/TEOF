from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

import teof.bootloader as bootloader
import teof.ideas as ideas_mod
import teof.commands.ideas as ideas_cmd


FIXED_NOW = "2025-01-01T00:00:00Z"


def _setup_idea_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path
    idea_dir = root / "docs" / "ideas"
    idea_dir.mkdir(parents=True, exist_ok=True)
    idea_path = idea_dir / "sample-idea.md"
    idea_path.write_text(
        """+++
id = "sample-idea"
title = "Sample Idea"
status = "draft"
created = "2024-10-01T00:00:00Z"
updated = "2024-10-01T00:00:00Z"
+++
# Sample Idea

Initial notes.
""",
        encoding="utf-8",
    )

    second_path = idea_dir / "backlog-idea.md"
    second_path.write_text(
        """+++
id = "backlog-idea"
title = "Backlog Candidate"
status = "promoted"
plan_id = "2024-12-01-backlog"
created = "2024-09-15T00:00:00Z"
updated = "2024-09-16T00:00:00Z"
+++
# Backlog Candidate

Already attached to plan.
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(bootloader, "ROOT", root, raising=False)
    monkeypatch.setattr(ideas_mod, "ROOT", root, raising=False)
    monkeypatch.setattr(ideas_mod, "IDEA_DIR", idea_dir, raising=False)
    monkeypatch.setattr(ideas_cmd, "IDEA_DIR", idea_dir, raising=False)
    monkeypatch.setattr(ideas_cmd, "DEFAULT_ROOT", root, raising=False)
    monkeypatch.setattr(ideas_mod, "_now_iso", lambda: FIXED_NOW, raising=False)
    monkeypatch.setattr(ideas_mod, "_now_utc", lambda: datetime(2025, 1, 1, tzinfo=timezone.utc), raising=False)

    return root


def test_teof_ideas_list_table(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup_idea_repo(tmp_path, monkeypatch)

    exit_code = bootloader.main(["ideas", "list"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "sample-idea" in output
    assert "Sample Idea" in output


def test_teof_ideas_list_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup_idea_repo(tmp_path, monkeypatch)

    exit_code = bootloader.main(["ideas", "list", "--format", "json"])
    assert exit_code == 0
    payload = capsys.readouterr().out
    assert '"count": 2' in payload
    assert '"id": "sample-idea"' in payload


def test_teof_ideas_mark_updates_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _setup_idea_repo(tmp_path, monkeypatch)

    exit_code = bootloader.main(
        [
            "ideas",
            "mark",
            "sample-idea",
            "--status",
            "triage",
            "--layer",
            "L4",
            "--systemic",
            "4",
        ]
    )
    assert exit_code == 0
    idea = ideas_mod.load_idea(root / "docs" / "ideas" / "sample-idea.md")
    assert idea.status == "triage"
    assert idea.meta.get("layers") == ["L4"]
    assert idea.meta.get("systemic") == [4]
    assert idea.meta.get("updated") == FIXED_NOW


def test_teof_ideas_promote_sets_plan_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _setup_idea_repo(tmp_path, monkeypatch)

    exit_code = bootloader.main(
        [
            "ideas",
            "promote",
            "sample-idea",
            "--plan-id",
            "2025-01-05-sample",
            "--note",
            "Ready for planner hand-off",
            "--layer",
            "L5",
            "--systemic",
            "5",
        ]
    )
    assert exit_code == 0
    idea = ideas_mod.load_idea(root / "docs" / "ideas" / "sample-idea.md")
    assert idea.status == "promoted"
    assert idea.meta.get("plan_id") == "2025-01-05-sample"
    assert idea.meta.get("layers") == ["L5"]
    assert idea.meta.get("systemic") == [5]
    notes = idea.meta.get("notes")
    assert isinstance(notes, list) and "Ready for planner hand-off" in notes


def test_teof_ideas_evaluate_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup_idea_repo(tmp_path, monkeypatch)

    exit_code = bootloader.main(["ideas", "evaluate", "--format", "json"])
    assert exit_code == 0
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["count"] == 1  # promoted idea excluded by default
    first = payload["ideas"][0]
    assert first["id"] == "sample-idea"
    assert first["score"] > 0
