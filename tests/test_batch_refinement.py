from __future__ import annotations

import subprocess
import json
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

    usage_dir = tmp_path / "usage"
    monkeypatch.setattr(batch_refinement.receipts_hygiene, "DEFAULT_USAGE_DIR", usage_dir)

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
        preset_calls["receipt"] = "_report/session/codex-1/session_brief/test.json"
        return {"summary": "pass", "receipt_path": preset_calls["receipt"]}

    monkeypatch.setattr(batch_refinement.session_brief, "_run_operator_preset", fake_preset)

    manifest = tmp_path / "AGENT_MANIFEST.json"
    manifest.write_text('{"agent_id": "codex-1"}', encoding="utf-8")
    monkeypatch.setattr(batch_refinement, "MANIFEST_PATH", manifest)

    log_dir = tmp_path / "logs"

    result = batch_refinement.run_batch(
        task="QUEUE-999",
        agent=None,
        pytest_args=["-k", "test_stub"],
        quiet=True,
        output=None,
        log_dir=log_dir,
        fail_on_missing=True,
        max_plan_latency=123.0,
    )

    assert calls[0][:3] == [batch_refinement.sys.executable, "-m", "pytest"]
    assert "-k" in calls[0]
    assert hygiene_called["kwargs"]["quiet"] is True
    assert preset_calls["agent"] == "codex-1"
    assert preset_calls["task"] == "QUEUE-999"
    assert result["receipts_hygiene"]["metrics"]["plans_missing_receipts"] == 0
    assert hygiene_called["kwargs"]["fail_on_missing"] is True
    assert hygiene_called["kwargs"]["max_plan_latency"] == 123.0
    log_path = Path(result["log_path"])
    if not log_path.is_absolute():
        log_path = (batch_refinement.ROOT / log_path).resolve()
    assert log_path.exists()
    data = json.loads(log_path.read_text(encoding="utf-8"))
    assert data["task"] == "QUEUE-999"
    assert data["agent"] == "codex-1"
    assert data["operator_preset"]["receipt_path"] == preset_calls["receipt"]


def test_batch_refinement_requires_agent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: DummyResult(0))
    monkeypatch.setattr(batch_refinement.receipts_hygiene, "run_hygiene", lambda **_: {})
    monkeypatch.setattr(batch_refinement.receipts_hygiene, "DEFAULT_USAGE_DIR", tmp_path / "usage")
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
    hygiene_kwargs = {}

    def fake_hygiene(**kwargs):
        hygiene_kwargs.update(kwargs)
        return {}

    monkeypatch.setattr(batch_refinement.receipts_hygiene, "run_hygiene", fake_hygiene)
    monkeypatch.setattr(batch_refinement.receipts_hygiene, "DEFAULT_USAGE_DIR", tmp_path / "usage")
    monkeypatch.setattr(batch_refinement.session_brief, "load_claim", lambda task: None)
    monkeypatch.setattr(batch_refinement.session_brief, "_run_operator_preset", lambda *a, **k: {})
    monkeypatch.setattr(batch_refinement, "MANIFEST_PATH", tmp_path / "AGENT_MANIFEST.json")
    (tmp_path / "AGENT_MANIFEST.json").write_text('{"agent_id": "codex-1"}', encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        batch_refinement.main([
            "--task",
            "QUEUE-101",
            "--quiet",
            "--fail-on-missing",
            "--max-plan-latency",
            "45",
        ])
    assert "pytest failed" in str(exc.value)


def test_batch_refinement_main_passes_hygiene_flags(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: DummyResult(0))
    hygiene_kwargs = {}

    def fake_hygiene(**kwargs):
        hygiene_kwargs.update(kwargs)
        return {}

    monkeypatch.setattr(batch_refinement.receipts_hygiene, "run_hygiene", fake_hygiene)
    monkeypatch.setattr(batch_refinement.receipts_hygiene, "DEFAULT_USAGE_DIR", tmp_path / "usage")
    monkeypatch.setattr(batch_refinement.session_brief, "load_claim", lambda task: {})
    monkeypatch.setattr(batch_refinement.session_brief, "_run_operator_preset", lambda *a, **k: {"summary": "pass", "receipt_path": "r"})
    manifest = tmp_path / "AGENT_MANIFEST.json"
    manifest.write_text('{"agent_id": "codex-1"}', encoding="utf-8")
    monkeypatch.setattr(batch_refinement, "MANIFEST_PATH", manifest)

    result = batch_refinement.main([
        "--task",
        "QUEUE-555",
        "--fail-on-missing",
        "--max-plan-latency",
        "30",
        "--quiet",
    ])
    assert result == 0
    assert hygiene_kwargs["fail_on_missing"] is True
    assert hygiene_kwargs["max_plan_latency"] == 30.0
