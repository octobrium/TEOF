import json
from pathlib import Path

import pytest

from tools.maintenance import readability_guard


def test_readability_guard_detects_failure(tmp_path, monkeypatch):
    path = tmp_path / "docs" / "bad.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("This sentence is extremely exceedingly verbose because it keeps on going without pause and therefore becomes unreadable." * 3, encoding="utf-8")

    monkeypatch.setattr(readability_guard, "ROOT", tmp_path)
    monkeypatch.setattr(readability_guard, "REPORT_DIR", tmp_path / "_report" / "readability")
    monkeypatch.setattr(readability_guard, "SUMMARY_PATH", readability_guard.REPORT_DIR / "summary-latest.json")

    exit_code = readability_guard.main([str(path.relative_to(tmp_path)), "--sentence-threshold", "10", "--word-threshold", "4"])
    assert exit_code == 1

    summary = json.loads((tmp_path / "_report" / "readability" / "summary-latest.json").read_text(encoding="utf-8"))
    assert summary["results"][0]["pass"] is False


def test_readability_guard_pass(tmp_path, monkeypatch):
    path = tmp_path / "docs" / "good.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Good sentences are short. They stay clear. Readers benefit.", encoding="utf-8")

    monkeypatch.setattr(readability_guard, "ROOT", tmp_path)
    monkeypatch.setattr(readability_guard, "REPORT_DIR", tmp_path / "_report" / "readability")
    monkeypatch.setattr(readability_guard, "SUMMARY_PATH", readability_guard.REPORT_DIR / "summary-latest.json")

    exit_code = readability_guard.main([str(path.relative_to(tmp_path))])
    assert exit_code == 0
