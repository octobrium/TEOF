from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tools.agent import receipts_hygiene


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_receipts_hygiene_runs_index_and_metrics(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root, check=True, stdout=subprocess.PIPE)

    plan_payload = {
        "version": 0,
        "plan_id": "2025-09-21-hygiene",
        "created": "2025-09-21T00:00:00Z",
        "actor": "tester",
        "summary": "Hygiene",
        "status": "queued",
        "steps": [],
        "checkpoint": {
            "description": "Pending",
            "owner": "tester",
            "status": "pending",
        },
        "receipts": [],
    }
    _write(repo_root / "_plans" / "2025-09-21-hygiene.plan.json", json.dumps(plan_payload))

    manager_report = repo_root / "_bus" / "messages" / "manager-report.jsonl"
    _write(manager_report, "")

    subprocess.run(["git", "add", "_plans", "_bus"], cwd=repo_root, check=True)

    monkeypatch.setattr(receipts_hygiene, "ROOT", repo_root)
    monkeypatch.setattr(receipts_hygiene, "DEFAULT_USAGE_DIR", repo_root / "_report" / "usage")

    output_dir = repo_root / "_report" / "usage"
    summary = receipts_hygiene.run_hygiene(root=repo_root, output_dir=output_dir, quiet=True)

    index_path = output_dir / "receipts-index-latest.jsonl"
    latency_path = output_dir / "receipts-latency-latest.jsonl"
    summary_path = output_dir / "receipts-hygiene-summary.json"
    assert index_path.exists()
    assert latency_path.exists()
    assert summary_path.exists()
    assert summary["metrics"]["plans_total"] >= 1
    assert "missing_plan_ids" in summary["metrics"]


def test_receipts_hygiene_cli(tmp_path: Path, monkeypatch, capsys) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root, check=True, stdout=subprocess.PIPE)
    _write(repo_root / "_plans" / "2025-09-21-empty.plan.json", json.dumps({
        "version": 0,
        "plan_id": "2025-09-21-empty",
        "created": "2025-09-21T01:00:00Z",
        "actor": "tester",
        "summary": "",
        "status": "queued",
        "steps": [],
        "checkpoint": {"description": "", "owner": "tester", "status": "pending"},
        "receipts": [],
    }))
    subprocess.run(["git", "add", "_plans"], cwd=repo_root, check=True)

    monkeypatch.setattr(receipts_hygiene, "ROOT", repo_root)
    monkeypatch.setattr(receipts_hygiene, "DEFAULT_USAGE_DIR", repo_root / "_report" / "usage")

    exit_code = receipts_hygiene.main([
        "--root",
        str(repo_root),
        "--output-dir",
        str(repo_root / "custom"),
    ])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Receipts hygiene summary" in out
    assert (repo_root / "custom" / "receipts-hygiene-summary.json").exists()


def test_run_hygiene_fail_on_missing(tmp_path: Path, monkeypatch) -> None:
    output_dir = tmp_path / "out"

    monkeypatch.setattr(receipts_hygiene.receipts_index, "_git_tracked_paths", lambda root: set())
    monkeypatch.setattr(receipts_hygiene.receipts_index, "build_index", lambda root, tracked: [])

    metrics_entries = [
        {
            "kind": "plan_latency",
            "plan_id": "2025-09-21-test",
            "latency_seconds": {"plan_to_first_receipt": 10.0},
            "missing_receipts": ["_report/plan.json"],
        }
    ]
    monkeypatch.setattr(
        receipts_hygiene.receipts_metrics, "build_metrics", lambda root, output: metrics_entries
    )

    with pytest.raises(SystemExit):
        receipts_hygiene.run_hygiene(
            root=tmp_path,
            output_dir=output_dir,
            quiet=True,
            fail_on_missing=True,
        )


def test_run_hygiene_fail_on_latency(tmp_path: Path, monkeypatch) -> None:
    output_dir = tmp_path / "out"

    monkeypatch.setattr(receipts_hygiene.receipts_index, "_git_tracked_paths", lambda root: set())
    monkeypatch.setattr(receipts_hygiene.receipts_index, "build_index", lambda root, tracked: [])

    metrics_entries = [
        {
            "kind": "plan_latency",
            "plan_id": "2025-09-21-slow",
            "latency_seconds": {"plan_to_first_receipt": 500.0, "note_to_first_receipt": None},
            "missing_receipts": [],
        }
    ]
    monkeypatch.setattr(
        receipts_hygiene.receipts_metrics, "build_metrics", lambda root, output: metrics_entries
    )

    with pytest.raises(SystemExit):
        receipts_hygiene.run_hygiene(
            root=tmp_path,
            output_dir=output_dir,
            quiet=True,
            max_plan_latency=100.0,
        )
