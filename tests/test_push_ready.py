import json
import subprocess
from pathlib import Path

import pytest

from tools.agent import push_ready


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.check_call(["git", "init"], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.check_call(["git", "checkout", "-b", "main"], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (repo / "README.md").write_text("demo", encoding="utf-8")
    subprocess.check_call(["git", "add", "README.md"], cwd=repo, stdout=subprocess.DEVNULL)
    subprocess.check_call(["git", "commit", "-m", "init"], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return repo


def test_check_clean_worktree(monkeypatch):
    monkeypatch.setattr(push_ready, "_run_git", lambda args: "")
    result = push_ready.check_clean_worktree()
    assert result.ok


def test_check_claims_detects_active(tmp_path, monkeypatch):
    claims_dir = tmp_path / "claims"
    claims_dir.mkdir()
    (claims_dir / "QUEUE-001.json").write_text(
        json.dumps({"agent_id": "codex-3", "status": "in_progress"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(push_ready, "CLAIMS_DIR", claims_dir)
    result = push_ready.check_claims("codex-3")
    assert not result.ok
    assert "QUEUE-001.json" in (result.details or "")


@pytest.mark.parametrize("active", [False, True])
def test_main_ready(tmp_path, monkeypatch, capsys, active):
    repo = _init_repo(tmp_path)
    claims_dir = repo / "_bus" / "claims"
    claims_dir.mkdir(parents=True)
    claim_path = claims_dir / "PLAN-123.json"
    payload = {"agent_id": "codex-3", "task_id": "PLAN-123", "plan_id": "2025-10-04-demo", "status": "in_progress" if active else "done"}
    claim_path.write_text(json.dumps(payload), encoding="utf-8")

    manifest = repo / "AGENT_MANIFEST.json"
    manifest.write_text(json.dumps({"agent_id": "codex-3"}), encoding="utf-8")

    plan_dir = repo / "_plans"
    plan_dir.mkdir(parents=True)
    (plan_dir / "2025-10-04-demo.plan.json").write_text(json.dumps({"plan_id": "2025-10-04-demo"}), encoding="utf-8")

    receipts_dir = repo / "_report" / "agent" / "codex-3" / "push-ready-checklist"
    receipts_dir.mkdir(parents=True)
    receipt = receipts_dir / "pytest.xml"
    receipt.write_text("<testsuite />", encoding="utf-8")

    subprocess.check_call([
        "git",
        "add",
        "_report/agent/codex-3/push-ready-checklist/pytest.xml",
        "_bus/claims/PLAN-123.json",
        "AGENT_MANIFEST.json",
        "_plans/2025-10-04-demo.plan.json",
    ], cwd=repo, stdout=subprocess.DEVNULL)
    subprocess.check_call(["git", "commit", "-m", "add readiness fixtures"], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    monkeypatch.setattr(push_ready, "ROOT", repo)
    monkeypatch.setattr(push_ready, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(push_ready, "MANIFEST_PATH", manifest)

    exit_code = push_ready.main(["--require-test", "_report/agent/codex-3/push-ready-checklist/pytest.xml"])
    stdout = capsys.readouterr().out
    payload = stdout[stdout.index("{") :]
    captured = json.loads(payload)

    if active:
        assert exit_code == 1
        assert not captured["ready"]
    else:
        assert exit_code == 0
        assert captured["ready"]
