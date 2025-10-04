import json
from importlib import reload
from pathlib import Path

import pytest

import scripts.ci.check_plans as check_plans


@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    root = tmp_path
    (root / "_plans").mkdir(parents=True, exist_ok=True)
    (root / "_bus" / "claims").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(check_plans, "ROOT", root)
    # force main() to re-discover plans from patched ROOT
    reload(check_plans)
    monkeypatch.setattr(check_plans, "ROOT", root)
    return root


def write_plan(
    root: Path,
    *,
    actor: str,
    status: str = "in_progress",
    plan_id: str = "2025-09-18-claim-guard",
) -> Path:
    plan_path = root / "_plans" / f"{plan_id}.plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "version": 0,
                "plan_id": plan_id,
                "created": "2025-09-18T00:00:00Z",
                "actor": actor,
                "summary": "Test plan",
                "status": status,
                "layer": "L5",
                "systemic_scale": 5,
                "ocers_target": "Observation↑",
                "steps": [
                    {"id": "S1", "title": "Step", "status": "queued"}
                ],
                "links": [
                    {"type": "bus", "ref": "_bus/claims/QUEUE-999.json"}
                ],
                "checkpoint": {
                    "description": "Test checkpoint",
                    "owner": actor,
                    "status": "pending",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return plan_path


def write_claim(root: Path, *, agent: str, status: str = "active") -> Path:
    claim_path = root / "_bus" / "claims" / "QUEUE-999.json"
    claim_path.write_text(
        json.dumps(
            {
                "task_id": "QUEUE-999",
                "agent_id": agent,
                "branch": f"agent/{agent}/queue-999",
                "status": status,
                "claimed_at": "2025-09-18T00:00:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return claim_path


def test_check_plans_flags_claim_mismatch(tmp_repo, monkeypatch):
    write_plan(tmp_repo, actor="codex-4")
    write_claim(tmp_repo, agent="codex-3", status="active")
    monkeypatch.setenv("PYTHONPATH", str(tmp_repo))
    rc = check_plans.main()
    assert rc == 1


def test_check_plans_allows_matching_claim(tmp_repo, monkeypatch):
    write_plan(tmp_repo, actor="codex-4")
    write_claim(tmp_repo, agent="codex-4", status="active")
    monkeypatch.setenv("PYTHONPATH", str(tmp_repo))
    rc = check_plans.main()
    assert rc == 0


def test_check_plans_ignores_terminal_claim(tmp_repo, monkeypatch):
    write_plan(tmp_repo, actor="codex-4")
    write_claim(tmp_repo, agent="codex-3", status="done")
    monkeypatch.setenv("PYTHONPATH", str(tmp_repo))
    rc = check_plans.main()
    assert rc == 0
