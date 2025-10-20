from __future__ import annotations

import json
import subprocess
from pathlib import Path

from tools.agent import receipts_index


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_receipts_index_generates_entries(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root, check=True, stdout=subprocess.PIPE)

    # Plan referencing a receipt.
    plan_payload = {
        "version": 0,
        "plan_id": "2025-09-21-sample",
        "created": "2025-09-21T00:00:00Z",
        "actor": "tester",
        "summary": "Sample plan",
        "status": "in_progress",
        "steps": [
            {
                "id": "S1",
                "title": "Do thing",
                "status": "done",
                "receipts": [
                    "_report/agent/tester/receipt.json"
                ],
            }
        ],
        "checkpoint": {
            "description": "Ensure validator passes",
            "owner": "tester",
            "status": "pending",
        },
        "receipts": [
            "_report/agent/tester/plan-level.json"
        ],
        "links": [],
    }
    plan_path = repo_root / "_plans" / "2025-09-21-sample.plan.json"
    write(plan_path, json.dumps(plan_payload))

    receipt_plan_level = repo_root / "_report" / "agent" / "tester" / "plan-level.json"
    write(receipt_plan_level, "{}\n")
    receipt_step = repo_root / "_report" / "agent" / "tester" / "receipt.json"
    write(receipt_step, "{}\n")

    manager_report = repo_root / "_bus" / "messages" / "manager-report.jsonl"
    write(
        manager_report,
        json.dumps(
            {
                "ts": "2025-09-21T01:00:00Z",
                "from": "codex-1",
                "type": "status",
                "task_id": "PLAN-2025-09-21-sample",
                "summary": "Sample update",
                "receipts": ["_report/agent/tester/receipt.json"],
                "meta": {"plan_id": "2025-09-21-sample"},
            }
        )
        + "\n",
    )

    subprocess.run(["git", "add", "_plans", "_report", "_bus"], cwd=repo_root, check=True)

    monkeypatch.setattr(receipts_index, "ROOT", repo_root)
    monkeypatch.setattr(receipts_index, "PLANS_DIR", repo_root / "_plans")
    monkeypatch.setattr(receipts_index, "REPORT_DIR", repo_root / "_report")
    monkeypatch.setattr(receipts_index, "MANAGER_REPORT", repo_root / "_bus" / "messages" / "manager-report.jsonl")
    monkeypatch.setattr(receipts_index, "DEFAULT_USAGE_DIR", repo_root / "_report" / "usage")

    output_dir = repo_root / "_report" / "usage" / "receipts-index"
    exit_code = receipts_index.main(["--root", str(repo_root), "--output", "receipts-index"])
    assert exit_code == 0
    manifest_path = output_dir / "manifest.json"
    assert manifest_path.exists()

    payload = receipts_index.load_index_from_manifest(manifest_path)
    assert payload.summary["kind"] == "summary"
    assert payload.summary["counts"]["plans"] == 1

    assert payload.plans and payload.plans[0]["plan_id"] == "2025-09-21-sample"
    assert payload.plans[0]["missing_receipts"] == []

    matched = [entry for entry in payload.receipts if entry["path"].endswith("plan-level.json")]
    assert matched
    assert matched[0]["referenced_by"][0]["plan_id"] == "2025-09-21-sample"

    assert payload.manager_messages
    assert payload.manager_messages[0]["missing_receipts"] == []
    assert payload.manager_messages[0]["plan_id"] == "2025-09-21-sample"
