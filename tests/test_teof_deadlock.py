from __future__ import annotations

from pathlib import Path

import pytest

import teof.bootloader as bootloader
from teof.commands import deadlock as deadlock_mod


def _patch_git_status(monkeypatch: pytest.MonkeyPatch, status: str) -> None:
    monkeypatch.setattr(deadlock_mod, "_git_status", lambda root: status)


def test_teof_deadlock_detects_multi_plan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _patch_git_status(
        monkeypatch,
        "\n".join(
            [
                " M _plans/2025-09-17-agent-bus-awareness.plan.json",
                " M _plans/2025-09-17-agent-bus-watch.plan.json",
                " M docs/automation.md",
            ]
        ),
    )
    monkeypatch.setattr(deadlock_mod, "ROOT", tmp_path)
    exit_code = bootloader.main(
        [
            "deadlock",
            "--plan-threshold",
            "2",
            "--file-threshold",
            "2",
        ]
    )
    assert exit_code == 1
    out = capsys.readouterr().out
    assert "POTENTIAL DEADLOCK" in out
    assert "agent-bus-awareness" in out


def test_teof_deadlock_json_clear(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _patch_git_status(monkeypatch, " M docs/automation.md")
    monkeypatch.setattr(deadlock_mod, "ROOT", tmp_path)
    exit_code = bootloader.main(["deadlock", "--format", "json"])
    assert exit_code == 0
    payload = capsys.readouterr().out
    assert '"suspected_deadlock": false' in payload.lower()
