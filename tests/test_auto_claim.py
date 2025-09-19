import json
import os
import subprocess
from pathlib import Path

import pytest


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_auto_claim_dry_run(monkeypatch, tmp_path):
    plans = tmp_path / "_plans"
    claim_dir = tmp_path / "_bus" / "claims"

    write_json(
        plans / "2025-09-18-bus-message-claim-guard.plan.json",
        {
            "plan_id": "2025-09-18-bus-message-claim-guard",
            "actor": "codex-2",
            "summary": "Add claim guard",
            "status": "queued",
            "steps": [],
            "links": [{"type": "queue", "ref": "queue/012-bus-message-claim-guard.md"}],
        },
    )

    env = os.environ.copy()
    env["TEOF_ROOT"] = str(tmp_path)
    result = subprocess.run(
        ["python3", "-m", "tools.automation.auto_claim"],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    assert "DRY-RUN" in result.stdout
    assert not list(claim_dir.glob("*.json"))


def test_auto_claim_execute(monkeypatch, tmp_path):
    plans = tmp_path / "_plans"
    claim_dir = tmp_path / "_bus" / "claims"

    write_json(
        plans / "2025-09-18-bus-message-claim-guard.plan.json",
        {
            "plan_id": "2025-09-18-bus-message-claim-guard",
            "actor": "codex-2",
            "summary": "Add claim guard",
            "status": "queued",
            "steps": [],
            "links": [{"type": "queue", "ref": "queue/012-bus-message-claim-guard.md"}],
        },
    )

    env = os.environ.copy()
    env["TEOF_ROOT"] = str(tmp_path)
    subprocess.run(
        ["python3", "-m", "tools.automation.auto_claim", "--execute"],
        check=True,
        env=env,
    )

    claim_path = claim_dir / "QUEUE-012.json"
    assert claim_path.exists()
    payload = json.loads(claim_path.read_text(encoding="utf-8"))
    assert payload["agent_id"] == "codex-2"
    assert payload["status"] == "active"
    assert payload["plan_id"] == "2025-09-18-bus-message-claim-guard"

    plan_path = plans / "2025-09-18-bus-message-claim-guard.plan.json"
    plan_payload = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan_payload["status"] == "in_progress"
