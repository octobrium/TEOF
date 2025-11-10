from __future__ import annotations

import os
from types import SimpleNamespace
from pathlib import Path

from tools.onboarding import quickstart


def test_git_metadata_reports_repo_state(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    (repo_root / ".git").mkdir(parents=True)
    outputs = {
        ("git", "rev-parse", "HEAD"): "deadbeefcafebabe\n",
        ("git", "rev-parse", "--abbrev-ref", "HEAD"): "main\n",
        ("git", "status", "--short"): " M docs/example.md\n",
    }

    def fake_run(cmd, *, cwd: Path | None = None, capture: bool = False):
        assert cwd == repo_root
        return SimpleNamespace(stdout=outputs[tuple(cmd)], returncode=0)

    monkeypatch.setattr(quickstart, "ROOT", repo_root)
    monkeypatch.setattr(quickstart, "_run", fake_run)

    meta = quickstart._git_metadata()

    assert meta == {
        "head": "deadbeefcafebabe",
        "branch": "main",
        "status": "M docs/example.md",
        "dirty": True,
    }


def test_git_metadata_handles_missing_repo(monkeypatch, tmp_path):
    repo_root = tmp_path / "no_git"
    repo_root.mkdir()
    monkeypatch.setattr(quickstart, "ROOT", repo_root)

    assert quickstart._git_metadata() is None


def test_intent_metadata_reads_env(monkeypatch):
    monkeypatch.setenv("TEOF_PLAN_ID", "2025-11-10-scout")
    monkeypatch.setenv("TEOF_PLAN_STEP_ID", "step-1")
    monkeypatch.setenv("TEOF_TASK_ID", "ND-099")
    monkeypatch.setenv("TEOF_AGENT_ID", "codex-5")

    assert quickstart._intent_metadata() == {
        "TEOF_PLAN_ID": "2025-11-10-scout",
        "TEOF_PLAN_STEP_ID": "step-1",
        "TEOF_TASK_ID": "ND-099",
        "TEOF_AGENT_ID": "codex-5",
    }


def test_intent_metadata_returns_none_when_unset(monkeypatch):
    for name in ("TEOF_PLAN_ID", "TEOF_PLAN_STEP_ID", "TEOF_TASK_ID", "TEOF_AGENT_ID"):
        monkeypatch.delenv(name, raising=False)

    assert quickstart._intent_metadata() is None
