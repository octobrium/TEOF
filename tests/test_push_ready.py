import json
import subprocess
from pathlib import Path

import pytest

from tools.agent import push_ready
from tools.planner import evidence_scope as planner_evidence
from tools.planner import validate as planner_validate


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.check_call(["git", "init"], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.check_call(["git", "checkout", "-b", "main"], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (repo / "README.md").write_text("demo", encoding="utf-8")
    subprocess.check_call(["git", "add", "README.md"], cwd=repo, stdout=subprocess.DEVNULL)
    subprocess.check_call(["git", "commit", "-m", "init"], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return repo


def _seed_plan_with_evidence(repo: Path, plan_id: str, *, with_receipt: bool) -> Path:
    plan_dir = repo / "_plans"
    plan_dir.mkdir(parents=True, exist_ok=True)
    scope = {
        "internal": [{"ref": "docs/architecture.md", "summary": "Repo map"}],
        "external": [{"ref": "https://example.org/reference", "summary": "Field study"}],
        "comparative": [{"ref": "https://example.org/trend", "summary": "Comparative trend"}],
    }
    receipts = []
    if with_receipt:
        receipt_rel = f"_report/evidence/{plan_id}/survey.json"
        receipt_path = repo / receipt_rel
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text("{}", encoding="utf-8")
        receipts.append(receipt_rel)
    if receipts:
        scope["receipts"] = receipts
    payload = {
        "version": 1,
        "plan_id": plan_id,
        "created": "2025-10-05T00:00:00Z",
        "actor": "tester",
        "summary": "Evidence plan",
        "status": "in_progress" if with_receipt else "queued",
        "impact_ref": plan_id,
        "layer": "L4",
        "systemic_scale": 5,
        "systemic_targets": ["S4", "S5"],
        "layer_targets": ["L4", "L5"],
        "steps": [
            {
                "id": "S1",
                "title": "Observe",
                "status": "in_progress" if with_receipt else "queued",
                "notes": "",
                "receipts": [],
            }
        ],
        "checkpoint": {
            "description": "Ensure evidence captured",
            "owner": "tester",
            "status": "pending",
        },
        "receipts": [],
        "links": [],
        "evidence_scope": scope,
    }
    plan_path = plan_dir / f"{plan_id}.plan.json"
    plan_path.write_text(json.dumps(payload), encoding="utf-8")
    subprocess.check_call(
        ["git", "add", plan_path.relative_to(repo).as_posix()],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if with_receipt:
        subprocess.check_call(
            ["git", "add", f"_report/evidence/{plan_id}/survey.json"],
            cwd=repo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    subprocess.check_call(["git", "commit", "-m", f"seed plan {plan_id}"], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return plan_path


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


def test_push_ready_evidence_guard_success(tmp_path, monkeypatch, capsys):
    repo = _init_repo(tmp_path)
    manifest = repo / "AGENT_MANIFEST.json"
    manifest.write_text(json.dumps({"agent_id": "codex-3"}), encoding="utf-8")
    subprocess.check_call(
        ["git", "add", "AGENT_MANIFEST.json"],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.check_call(
        ["git", "commit", "-m", "seat manifest"],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    plan_id = "2025-10-05-evidence"
    _seed_plan_with_evidence(repo, plan_id, with_receipt=True)

    monkeypatch.setattr(push_ready, "ROOT", repo)
    monkeypatch.setattr(push_ready, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(push_ready, "CLAIMS_DIR", repo / "_bus" / "claims")
    monkeypatch.setattr(planner_evidence, "ROOT", repo)
    monkeypatch.setattr(planner_evidence, "PLANS_DIR", repo / "_plans")
    monkeypatch.setattr(planner_validate, "ROOT", repo)
    monkeypatch.setattr(planner_validate, "PLANS_DIR", repo / "_plans")
    planner_validate._git_tracked_paths.cache_clear()

    exit_code = push_ready.main(["--agent", "codex-3", "--require-evidence-plan", plan_id])
    stdout = capsys.readouterr().out
    payload = json.loads(stdout[stdout.index("{") :])
    assert exit_code == 0
    assert payload["ready"]


def test_check_paths_allows_untracked_report(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    receipt_path = repo / "_report" / "agent" / "codex-3" / "run.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(push_ready, "ROOT", repo)

    result = push_ready.check_paths("receipts_exist", [receipt_path])
    assert result.ok


def test_push_ready_evidence_guard_failure(tmp_path, monkeypatch, capsys):
    repo = _init_repo(tmp_path)
    manifest = repo / "AGENT_MANIFEST.json"
    manifest.write_text(json.dumps({"agent_id": "codex-3"}), encoding="utf-8")
    subprocess.check_call(
        ["git", "add", "AGENT_MANIFEST.json"],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.check_call(
        ["git", "commit", "-m", "seat manifest"],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    plan_id = "2025-10-06-evidence"
    _seed_plan_with_evidence(repo, plan_id, with_receipt=False)

    monkeypatch.setattr(push_ready, "ROOT", repo)
    monkeypatch.setattr(push_ready, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(push_ready, "CLAIMS_DIR", repo / "_bus" / "claims")
    monkeypatch.setattr(planner_evidence, "ROOT", repo)
    monkeypatch.setattr(planner_evidence, "PLANS_DIR", repo / "_plans")
    monkeypatch.setattr(planner_validate, "ROOT", repo)
    monkeypatch.setattr(planner_validate, "PLANS_DIR", repo / "_plans")
    planner_validate._git_tracked_paths.cache_clear()

    exit_code = push_ready.main(["--agent", "codex-3", "--require-evidence-plan", plan_id])
    stdout = capsys.readouterr().out
    payload = json.loads(stdout[stdout.index("{") :])
    assert exit_code == 1
    assert not payload["ready"]
