from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List

import pytest

from tools.agent import batch_refinement


class DummyResult:
    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode


def test_batch_refinement_runs_components(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: List[List[str]] = []

    def fake_run(cmd, cwd=None):
        calls.append(cmd)
        return DummyResult(0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    hygiene_called = {}

    def fake_hygiene(**kwargs):
        hygiene_called["kwargs"] = kwargs
        return {"metrics": {"plans_missing_receipts": 0}}

    monkeypatch.setattr(batch_refinement.receipts_hygiene, "run_hygiene", fake_hygiene)

    def fake_load_claim(task):
        return {"task_id": task, "agent_id": "codex-1", "status": "active"}

    monkeypatch.setattr(batch_refinement.session_brief, "load_claim", fake_load_claim)

    preset_calls = {}

    def fake_preset(agent_id, task, claim, output=None):
        preset_calls["agent"] = agent_id
        preset_calls["task"] = task
        preset_calls["claim"] = claim
        preset_calls["output"] = output
        return {"summary": "pass", "receipt_path": "_report/session/codex-1/session_brief/test.json"}

    monkeypatch.setattr(batch_refinement.session_brief, "_run_operator_preset", fake_preset)

    manifest = tmp_path / "AGENT_MANIFEST.json"
    manifest.write_text('{"agent_id": "codex-1"}', encoding="utf-8")
    monkeypatch.setattr(batch_refinement, "MANIFEST_PATH", manifest)

    result = batch_refinement.run_batch(
        task="QUEUE-999",
        agent=None,
        pytest_args=["-k", "test_stub"],
        quiet=True,
        output=None,
    )

    assert calls[0][:3] == [batch_refinement.sys.executable, "-m", "pytest"]
    assert "-k" in calls[0]
    assert hygiene_called["kwargs"]["quiet"] is True
    assert preset_calls["agent"] == "codex-1"
    assert preset_calls["task"] == "QUEUE-999"
    assert result["receipts_hygiene"]["metrics"]["plans_missing_receipts"] == 0


def test_batch_refinement_requires_agent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: DummyResult(0))
    monkeypatch.setattr(batch_refinement.receipts_hygiene, "run_hygiene", lambda **_: {})
    monkeypatch.setattr(batch_refinement.session_brief, "load_claim", lambda task: None)
    monkeypatch.setattr(batch_refinement.session_brief, "_run_operator_preset", lambda *a, **k: {})
    monkeypatch.setattr(batch_refinement, "MANIFEST_PATH", tmp_path / "missing.json")

    with pytest.raises(SystemExit):
        batch_refinement.run_batch(
            task="QUEUE-001",
            agent=None,
            pytest_args=[],
            quiet=True,
            output=None,
        )


def test_batch_refinement_main_propagates_pytest_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fail_run(cmd, cwd=None):
        return DummyResult(1)

    monkeypatch.setattr(subprocess, "run", fail_run)
    monkeypatch.setattr(batch_refinement.receipts_hygiene, "run_hygiene", lambda **_: {})
    monkeypatch.setattr(batch_refinement.session_brief, "load_claim", lambda task: None)
    monkeypatch.setattr(batch_refinement.session_brief, "_run_operator_preset", lambda *a, **k: {})
    monkeypatch.setattr(batch_refinement, "MANIFEST_PATH", tmp_path / "AGENT_MANIFEST.json")
    (tmp_path / "AGENT_MANIFEST.json").write_text('{"agent_id": "codex-1"}', encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        batch_refinement.main(["--task", "QUEUE-101", "--quiet"])
    assert "pytest failed" in str(exc.value)
