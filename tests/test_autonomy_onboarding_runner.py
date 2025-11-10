from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from tools.autonomy import onboarding_runner


def _ns(**kwargs):
    return argparse.Namespace(**kwargs)


def test_onboarding_runner_creates_receipt(monkeypatch, tmp_path):
    agent_id = "codex-9"

    # Repoint repo roots to the temp dir
    monkeypatch.setattr(onboarding_runner, "ROOT", tmp_path)
    automation_dir = tmp_path / "automation"
    monkeypatch.setattr(onboarding_runner, "AUTOMATION_RECEIPT_DIR", automation_dir)
    session_dir = tmp_path / "_report" / "session"
    monkeypatch.setattr(onboarding_runner, "SESSION_DIR", session_dir)
    session_tail = session_dir / agent_id / "manager-report-tail.txt"
    session_tail.parent.mkdir(parents=True, exist_ok=True)
    session_tail.write_text("# manager tail\n# captured_at=2025-11-09T00:00:00Z\n", encoding="utf-8")

    # Stub dependencies
    monkeypatch.setattr(
        onboarding_runner.session_guard,
        "resolve_agent_id",
        lambda explicit: agent_id,
    )
    called = {}

    def fake_session_boot(argv):
        called["session_boot"] = argv
        return 0

    monkeypatch.setattr(onboarding_runner.session_boot, "main", fake_session_boot)

    syscheck_payload = {
        "python_version": "3.10.8",
        "python_path": "/usr/bin/python3",
        "pip_path": "pip 25.0",
        "pytest_path": "/usr/local/bin/pytest",
        "issues": [],
    }
    monkeypatch.setattr(onboarding_runner, "_run_syscheck", lambda: syscheck_payload)

    artifact_dir = tmp_path / "artifacts" / "systemic_out" / "20250101T000000Z"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    eval_receipt = tmp_path / "_report" / "usage" / "onboarding" / "tier1.json"
    eval_receipt.parent.mkdir(parents=True, exist_ok=True)
    eval_receipt.write_text("{}", encoding="utf-8")
    metadata = artifact_dir / "metadata.json"
    metadata.write_text("{}", encoding="utf-8")

    tier1_result = {
        "artifact_dir": artifact_dir,
        "ensembles": ["001.ensemble.json"],
        "score_text": "ensemble_count=10",
        "document_count": 10,
        "quickstart_receipt": None,
        "quickstart_git": None,
        "quickstart_intent": None,
        "eval_receipt": eval_receipt,
        "metadata_path": metadata,
    }
    monkeypatch.setattr(onboarding_runner, "_run_teof_eval", lambda skip: tier1_result)

    args = _ns(agent=None, focus="automation", skip_session=False, skip_install=False)
    assert onboarding_runner.run(args) == 0

    receipts = list(automation_dir.glob("*.json"))
    assert receipts, "expected automation receipt to be created"
    payload = json.loads(receipts[0].read_text(encoding="utf-8"))
    assert payload["agent_id"] == agent_id
    assert payload["syscheck"] == syscheck_payload
    assert payload["tier1_eval"]["artifact_dir"].endswith("artifacts/systemic_out/20250101T000000Z")
    assert automation_dir.joinpath("latest.json").exists()
    assert called["session_boot"][0:2] == ["--agent", agent_id]


def test_onboarding_runner_fails_when_syscheck_reports_issue(monkeypatch):
    monkeypatch.setattr(
        onboarding_runner.session_guard,
        "resolve_agent_id",
        lambda explicit: "codex-9",
    )
    monkeypatch.setattr(onboarding_runner, "_run_syscheck", lambda: {"issues": ["bad python"]})
    with pytest.raises(SystemExit):
        onboarding_runner.run(
            _ns(agent=None, focus=None, skip_session=True, skip_install=False)
        )
