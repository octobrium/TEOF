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

    output_path = repo_root / "_report" / "usage" / "receipts-index.jsonl"
    exit_code = receipts_index.main(["--root", str(repo_root), "--output", "receipts-index.jsonl"])
    assert exit_code == 0
    assert output_path.exists()

    lines = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    kinds = {entry["kind"] for entry in lines}
    assert {"summary", "plan", "receipt", "manager_message"} <= kinds

    plan_entries = [entry for entry in lines if entry["kind"] == "plan"]
    assert plan_entries and plan_entries[0]["plan_id"] == "2025-09-21-sample"
    assert plan_entries[0]["missing_receipts"] == []

    receipt_entries = [entry for entry in lines if entry["kind"] == "receipt"]
    matched = [entry for entry in receipt_entries if entry["path"].endswith("plan-level.json")]
    assert matched
    assert matched[0]["referenced_by"][0]["plan_id"] == "2025-09-21-sample"

    manager_entries = [entry for entry in lines if entry["kind"] == "manager_message"]
    assert manager_entries
    assert manager_entries[0]["missing_receipts"] == []
    assert manager_entries[0]["plan_id"] == "2025-09-21-sample"
