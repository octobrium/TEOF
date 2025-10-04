import json
import subprocess
from pathlib import Path

import pytest

from tools.agent import assignment_locator


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.check_call(["git", "init"], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.check_call(["git", "checkout", "-b", "main"], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (repo / "README.md").write_text("demo", encoding="utf-8")
    subprocess.check_call(["git", "add", "README.md"], cwd=repo, stdout=subprocess.DEVNULL)
    subprocess.check_call(["git", "commit", "-m", "init"], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return repo


def test_run_check_missing_plan(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    claims_dir = repo / "_bus" / "claims"
    claims_dir.mkdir(parents=True)
    claim_path = claims_dir / "PLAN-001.json"
    payload = {
        "agent_id": "codex-3",
        "task_id": "PLAN-001",
        "plan_id": "2025-10-04-missing",
        "status": "active",
    }
    claim_path.write_text(json.dumps(payload), encoding="utf-8")

    manifest = repo / "AGENT_MANIFEST.json"
    manifest.write_text(json.dumps({"agent_id": "codex-3"}), encoding="utf-8")

    monkeypatch.setattr(assignment_locator, "ROOT", repo)
    monkeypatch.setattr(assignment_locator, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(assignment_locator, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(assignment_locator, "PLANS_DIR", repo / "_plans")

    ok, missing = assignment_locator.run_check("codex-3")
    assert not ok
    assert missing and missing[0]["issue"] == "plan_missing"


def test_run_check_ok(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    claims_dir = repo / "_bus" / "claims"
    claims_dir.mkdir(parents=True)
    plan_dir = repo / "_plans"
    plan_dir.mkdir(parents=True)
    plan_id = "2025-10-04-present"
    (plan_dir / f"{plan_id}.plan.json").write_text(json.dumps({"plan_id": plan_id}), encoding="utf-8")

    claim_path = claims_dir / "PLAN-002.json"
    claim_path.write_text(
        json.dumps({
            "agent_id": "codex-3",
            "task_id": "PLAN-002",
            "plan_id": plan_id,
            "status": "active",
        }),
        encoding="utf-8",
    )

    manifest = repo / "AGENT_MANIFEST.json"
    manifest.write_text(json.dumps({"agent_id": "codex-3"}), encoding="utf-8")

    monkeypatch.setattr(assignment_locator, "ROOT", repo)
    monkeypatch.setattr(assignment_locator, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(assignment_locator, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(assignment_locator, "PLANS_DIR", plan_dir)

    ok, missing = assignment_locator.run_check("codex-3")
    assert ok
    assert missing == []
