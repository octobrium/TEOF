from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from teof import _paths


@pytest.fixture(name="repo_root")
def _repo_root(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    (tmp_path / "README.md").write_text("", encoding="utf-8")
    (tmp_path / "teof").mkdir()
    return tmp_path


@pytest.fixture(autouse=True)
def _override_root(repo_root: Path):
    original = _paths.repo_root()
    _paths.set_repo_root(repo_root)
    module = importlib.import_module("tools.behavioral.trials")
    importlib.reload(module)
    yield
    _paths.set_repo_root(original)
    importlib.reload(module)


def test_record_and_summary(repo_root: Path) -> None:
    module = importlib.import_module("tools.behavioral.trials")
    ts = datetime(2025, 11, 9, 23, 0, tzinfo=timezone.utc).isoformat()
    module.record_trial(
        trial_id="T01",
        plan_id="demo-plan",
        agent_id="codex-tier2",
        prompt="blind-test",
        result="pass",
        bes_score=0.83,
        receipt_path="docs/demo.md",
        ts=ts,
    )
    module.record_trial(
        trial_id="T02",
        plan_id="demo-plan",
        agent_id="codex-tier2",
        prompt="blind-test",
        result="fail",
        bes_score=0.42,
        receipt_path="docs/demo.md",
        ts=ts,
    )
    summary = module.summarise_trials(module.iter_trials())
    assert summary["total"] == 2
    assert summary["passed"] == 1
    assert summary["failed"] == 1
    assert summary["average_bes_score"] == pytest.approx(0.62, rel=1e-2)


def test_cli_summary_out(repo_root: Path, monkeypatch, capsys):
    module = importlib.import_module("tools.behavioral.trials")
    module.record_trial(
        trial_id="T10",
        plan_id="demo-plan",
        agent_id="codex-tier2",
        prompt="trial",
        result="pass",
        bes_score=0.9,
        receipt_path="docs/demo.md",
    )
    out_path = repo_root / "_report" / "usage" / "behavioral-trials" / "summary.json"
    rc = module.main(["summary", "--out", str(out_path), "--min-trials", "1"])
    assert rc == 0
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["total"] >= 1
