from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from tools.agent import receipts_index, receipts_metrics


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _set_mtime(path: Path, when: datetime) -> None:
    ts = when.timestamp()
    os.utime(path, (ts, ts))


def test_receipts_metrics_outputs_latencies(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root, check=True, stdout=subprocess.PIPE)

    plan_payload = {
        "version": 0,
        "plan_id": "2025-09-21-latency",
        "created": "2025-09-21T00:00:00Z",
        "actor": "tester",
        "summary": "Latency plan",
        "status": "in_progress",
        "steps": [
            {
                "id": "S1",
                "title": "Do work",
                "status": "done",
                "receipts": ["_report/agent/tester/receipt.json"],
            }
        ],
        "checkpoint": {
            "description": "Ensure latency metrics",
            "owner": "tester",
            "status": "pending",
        },
        "receipts": ["_report/agent/tester/plan.json"],
    }
    plan_path = repo_root / "_plans" / "2025-09-21-latency.plan.json"
    _write(plan_path, json.dumps(plan_payload))

    receipt_plan = repo_root / "_report" / "agent" / "tester" / "plan.json"
    receipt_step = repo_root / "_report" / "agent" / "tester" / "receipt.json"
    _write(receipt_plan, "{}\n")
    _write(receipt_step, "{}\n")
    first_receipt_time = datetime(2025, 9, 21, 0, 30, tzinfo=timezone.utc)
    second_receipt_time = datetime(2025, 9, 21, 1, 0, tzinfo=timezone.utc)
    _set_mtime(receipt_plan, first_receipt_time)
    _set_mtime(receipt_step, second_receipt_time)

    manager_report = repo_root / "_bus" / "messages" / "manager-report.jsonl"
    _write(
        manager_report,
        json.dumps(
            {
                "ts": "2025-09-21T00:10:00Z",
                "from": "codex-1",
                "type": "note",
                "summary": "Reflection",
                "plan_id": "2025-09-21-latency",
                "receipts": [],
                "meta": {"plan_id": "2025-09-21-latency"},
            }
        )
        + "\n",
    )

    subprocess.run(["git", "add", "_plans", "_report", "_bus"], cwd=repo_root, check=True)

    monkeypatch.setattr(receipts_index, "ROOT", repo_root)
    monkeypatch.setattr(receipts_index, "PLANS_DIR", repo_root / "_plans")
    monkeypatch.setattr(receipts_index, "REPORT_DIR", repo_root / "_report")
    monkeypatch.setattr(receipts_index, "MANAGER_REPORT", manager_report)
    monkeypatch.setattr(receipts_index, "DEFAULT_USAGE_DIR", repo_root / "_report" / "usage")
    monkeypatch.setattr(receipts_metrics, "ROOT", repo_root)
    monkeypatch.setattr(receipts_metrics, "DEFAULT_USAGE_DIR", repo_root / "_report" / "usage")

    output_path = repo_root / "_report" / "usage" / "latency.jsonl"
    receipts_metrics.main(["--root", str(repo_root), "--output", str(output_path)])
    assert output_path.exists()

    lines = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert lines[0]["kind"] == "summary"
    plan_entry = next(entry for entry in lines if entry.get("kind") == "plan_latency")
    assert plan_entry["plan_id"] == "2025-09-21-latency"
    latencies = plan_entry["latency_seconds"]
    assert latencies["plan_to_first_receipt"] == 1800.0
    assert latencies["plan_to_last_receipt"] == 3600.0
    assert latencies["note_to_plan"] == 600.0
    assert latencies["note_to_first_receipt"] == 1200.0
    assert plan_entry["missing_receipts"] == []


def test_receipts_metrics_includes_non_report_receipts(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test Agent"], cwd=repo_root, check=True)

    plan_payload = {
        "version": 0,
        "plan_id": "2025-09-21-mixed",
        "created": "2025-09-21T00:00:00Z",
        "actor": "tester",
        "summary": "Mixed receipts",
        "status": "done",
        "steps": [],
        "checkpoint": {
            "description": "Ensure mixed receipts counted",
            "owner": "tester",
            "status": "satisfied",
        },
        "receipts": ["docs/note.md", "_report/agent/tester/late.json"],
    }
    plan_path = repo_root / "_plans" / "2025-09-21-mixed.plan.json"
    _write(plan_path, json.dumps(plan_payload))

    doc_receipt = repo_root / "docs" / "note.md"
    report_receipt = repo_root / "_report" / "agent" / "tester" / "late.json"
    _write(doc_receipt, "note")
    _write(report_receipt, "{}\n")

    subprocess.run(["git", "add", "_plans", "docs", "_report"], cwd=repo_root, check=True)
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = "2025-09-21T00:05:00Z"
    env["GIT_COMMITTER_DATE"] = "2025-09-21T00:05:00Z"
    subprocess.run(
        ["git", "commit", "-m", "seed mixed receipts"],
        cwd=repo_root,
        check=True,
        env=env,
        stdout=subprocess.PIPE,
    )

    _write(report_receipt, "{\"updated\": true}\n")
    _set_mtime(report_receipt, datetime(2025, 9, 21, 1, 0, tzinfo=timezone.utc))
    subprocess.run(["git", "add", "_report"], cwd=repo_root, check=True)
    later_env = os.environ.copy()
    later_env["GIT_AUTHOR_DATE"] = "2025-09-21T01:00:00Z"
    later_env["GIT_COMMITTER_DATE"] = "2025-09-21T01:00:00Z"
    subprocess.run(
        ["git", "commit", "-m", "plan receipt update"],
        cwd=repo_root,
        check=True,
        env=later_env,
        stdout=subprocess.PIPE,
    )

    _set_mtime(doc_receipt, datetime(2025, 9, 21, 2, 0, tzinfo=timezone.utc))

    monkeypatch.setattr(receipts_index, "ROOT", repo_root)
    monkeypatch.setattr(receipts_index, "PLANS_DIR", repo_root / "_plans")
    monkeypatch.setattr(receipts_index, "REPORT_DIR", repo_root / "_report")
    monkeypatch.setattr(receipts_index, "MANAGER_REPORT", repo_root / "_bus" / "messages" / "manager-report.jsonl")
    monkeypatch.setattr(receipts_index, "DEFAULT_USAGE_DIR", repo_root / "_report" / "usage")
    monkeypatch.setattr(receipts_metrics, "ROOT", repo_root)
    monkeypatch.setattr(receipts_metrics, "DEFAULT_USAGE_DIR", repo_root / "_report" / "usage")

    entries = receipts_metrics.build_metrics(repo_root, output=None)
    plan_entries = [entry for entry in entries if entry.get("kind") == "plan_latency"]
    plan_entry = next(entry for entry in plan_entries if entry.get("plan_id") == "2025-09-21-mixed")

    latencies = plan_entry["latency_seconds"]
    assert latencies["plan_to_first_receipt"] == 300.0
    assert latencies["plan_to_last_receipt"] == 3600.0
    assert plan_entry["missing_receipts"] == []


def test_receipts_metrics_stdout(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root, check=True, stdout=subprocess.PIPE)

    plan_payload = {
        "version": 0,
        "plan_id": "2025-09-21-empty",
        "created": "2025-09-21T02:00:00Z",
        "actor": "tester",
        "summary": "No receipts yet",
        "status": "queued",
        "steps": [],
        "checkpoint": {
            "description": "Pending",
            "owner": "tester",
            "status": "pending",
        },
        "receipts": [],
    }
    _write(repo_root / "_plans" / "2025-09-21-empty.plan.json", json.dumps(plan_payload))
    subprocess.run(["git", "add", "_plans"], cwd=repo_root, check=True)

    manager_report = repo_root / "_bus" / "messages" / "manager-report.jsonl"
    monkeypatch.setattr(receipts_index, "ROOT", repo_root)
    monkeypatch.setattr(receipts_index, "PLANS_DIR", repo_root / "_plans")
    monkeypatch.setattr(receipts_index, "REPORT_DIR", repo_root / "_report")
    monkeypatch.setattr(receipts_index, "MANAGER_REPORT", manager_report)
    monkeypatch.setattr(receipts_index, "DEFAULT_USAGE_DIR", repo_root / "_report" / "usage")
    monkeypatch.setattr(receipts_metrics, "ROOT", repo_root)
    monkeypatch.setattr(receipts_metrics, "DEFAULT_USAGE_DIR", repo_root / "_report" / "usage")

    entries = receipts_metrics.build_metrics(repo_root, output=None)
    assert entries[0]["kind"] == "summary"
    plan_entries = [entry for entry in entries if entry.get("kind") == "plan_latency"]
    assert plan_entries and plan_entries[0]["plan_id"] == "2025-09-21-empty"
    assert plan_entries[0]["missing_receipts"] == []
