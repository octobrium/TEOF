import json
import subprocess
from pathlib import Path

import pytest

from tools.planner import evidence_scope
from tools.planner import validate as planner_validate


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.check_call(
        ["git", "init"],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.check_call(
        ["git", "checkout", "-b", "main"],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return repo


def _seed_plan(repo: Path, *, plan_id: str, with_receipt: bool) -> None:
    plan_dir = repo / "_plans"
    plan_dir.mkdir(parents=True, exist_ok=True)
    scope = {
        "internal": [{"ref": "docs/architecture.md", "summary": "Repo layout"}],
        "external": [{"ref": "https://example.org/field", "summary": "Field study"}],
        "comparative": [{"ref": "https://example.org/trend", "summary": "Trend"}],
        "receipts": [],
    }
    if with_receipt:
        receipt_rel = f"_report/agent/demo/{plan_id}/evidence.json"
        receipt_path = repo / receipt_rel
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text("{}", encoding="utf-8")
        scope["receipts"].append(receipt_rel)
        subprocess.check_call(
            ["git", "add", receipt_rel],
            cwd=repo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    payload = {
        "version": 1,
        "plan_id": plan_id,
        "created": "2025-11-10T00:00:00Z",
        "actor": "tester",
        "summary": "Demo plan",
        "status": "in_progress",
        "impact_ref": plan_id,
        "layer": "L4",
        "systemic_scale": 6,
        "systemic_targets": ["S4", "S6"],
        "layer_targets": ["L4"],
        "steps": [
            {
                "id": "S1",
                "title": "Observe",
                "status": "in_progress",
                "notes": "",
                "receipts": [],
            }
        ],
        "checkpoint": {
            "description": "Evidence guard",
            "owner": "tester",
            "status": "pending",
        },
        "receipts": [],
        "links": [],
        "evidence_scope": scope,
    }
    plan_path = plan_dir / f"{plan_id}.plan.json"
    plan_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    subprocess.check_call(
        ["git", "add", plan_path.relative_to(repo).as_posix()],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


@pytest.fixture()
def repo_with_plans(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str, str]:
    repo = _init_repo(tmp_path)
    plan_ok = "2025-11-10-evidence-cli"
    plan_missing = "2025-11-10-evidence-missing"
    _seed_plan(repo, plan_id=plan_ok, with_receipt=True)
    _seed_plan(repo, plan_id=plan_missing, with_receipt=False)
    monkeypatch.setattr(evidence_scope, "ROOT", repo)
    monkeypatch.setattr(evidence_scope, "PLANS_DIR", repo / "_plans")
    monkeypatch.setattr(evidence_scope, "RECEIPT_DIR", repo / "_report" / "usage" / "evidence-scope")
    monkeypatch.setattr(planner_validate, "ROOT", repo)
    monkeypatch.setattr(planner_validate, "PLANS_DIR", repo / "_plans")
    planner_validate._git_tracked_paths.cache_clear()
    return repo, plan_ok, plan_missing


def test_scan_plans_reports_ok(repo_with_plans: tuple[Path, str, str]) -> None:
    _, plan_id, _ = repo_with_plans
    reports = evidence_scope.scan_plans(plan_ids=[plan_id])
    assert len(reports) == 1
    report = reports[0]
    assert report.plan_id == plan_id
    assert report.ok
    assert report.counts["internal"] == 1


def test_evidence_scope_cli_writes_receipt(tmp_path: Path, repo_with_plans: tuple[Path, str, str], capsys) -> None:
    repo, plan_id, _ = repo_with_plans
    receipt_dir = repo / "_report" / "usage" / "evidence-test"
    exit_code = evidence_scope.main(
        [
            "--plan",
            plan_id,
            "--receipt-dir",
            str(receipt_dir),
        ]
    )
    assert exit_code == 0
    stdout = capsys.readouterr().out
    payload = json.loads(stdout)
    assert payload["plans"][0]["plan_id"] == plan_id
    receipts = list(receipt_dir.glob("evidence-scope-*.json"))
    assert receipts, "expected receipt artifact"
    latest = json.loads((receipt_dir / "latest.json").read_text(encoding="utf-8"))
    assert latest["receipt"].endswith(receipts[0].name)


def test_evidence_scope_cli_fail_on_missing(repo_with_plans: tuple[Path, str, str]) -> None:
    _, _, missing_plan = repo_with_plans
    exit_code = evidence_scope.main(
        [
            "--plan",
            missing_plan,
            "--no-receipt",
            "--fail-on-missing",
        ]
    )
    assert exit_code == 2


def test_evidence_scope_cli_fail_on_missing_receipts(repo_with_plans: tuple[Path, str, str]) -> None:
    _, _, missing_plan = repo_with_plans
    exit_code = evidence_scope.main(
        [
            "--plan",
            missing_plan,
            "--no-receipt",
            "--fail-on-missing-receipts",
        ]
    )
    assert exit_code == 2
