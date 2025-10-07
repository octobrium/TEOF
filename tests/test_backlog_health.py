from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.agent import backlog_health


@pytest.fixture()
def queue_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "queue"
    directory.mkdir()
    (directory / "005-sample-task.md").write_text(
        """# Task: Sample backlog item
Coordinate: S3:L5
OCERS Target: Observation↑ Coherence↑
""",
        encoding="utf-8",
    )
    (directory / "010-followup.md").write_text(
        """# Task: Secondary task
Coordinate: S2:L4
OCERS Target: Observation↑ Ethics↑
""",
        encoding="utf-8",
    )
    return directory


def _next_dev_file(tmp_path: Path, items: list[dict[str, object]], updated: str = "2025-10-05T00:00:00Z") -> Path:
    payload = {
        "version": 0,
        "updated": updated,
        "items": items,
    }
    path = tmp_path / "next-development.todo.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def test_compute_metrics_no_breach(tmp_path: Path, queue_dir: Path) -> None:
    data = {
        "updated": "2025-10-05T00:00:00Z",
        "items": [
            {"id": "ND-001", "status": "done"},
            {
                "id": "ND-002",
                "status": "pending",
                "priority": "high",
                "layer": "L5",
                "systemic_scale": 5,
                "plan_suggestion": "plan-1",
            },
        ],
    }
    metrics = backlog_health.compute_metrics(
        data,
        threshold=1,
        queue_dir=queue_dir,
        candidate_limit=2,
    )
    assert metrics["pending_count"] == 1
    assert metrics["pending_threshold_breached"] is False
    assert metrics["replenishment_candidates"] == []
    assert metrics["status_counts"]["done"] == 1
    assert metrics["pending_items"][0]["id"] == "ND-002"


def test_compute_metrics_with_breach_and_candidates(tmp_path: Path, queue_dir: Path) -> None:
    data = {
        "updated": "2025-10-05T00:00:00Z",
        "items": [
            {"id": "ND-010", "status": "done"},
        ],
    }
    metrics = backlog_health.compute_metrics(
        data,
        threshold=2,
        queue_dir=queue_dir,
        candidate_limit=2,
    )
    assert metrics["pending_count"] == 0
    assert metrics["pending_threshold_breached"] is True
    assert len(metrics["replenishment_candidates"]) == 2
    first = metrics["replenishment_candidates"][0]
    assert first["queue_id"] == "005"
    assert first["title"].startswith("Sample")


def test_main_writes_receipt_and_fail_on_breach(tmp_path: Path, queue_dir: Path) -> None:
    next_dev = _next_dev_file(tmp_path, items=[])
    receipt_path = tmp_path / "receipt.json"
    exit_code = backlog_health.main(
        [
            "--next-development",
            str(next_dev),
            "--queue-dir",
            str(queue_dir),
            "--threshold",
            "1",
            "--output",
            str(receipt_path),
            "--fail-on-breach",
        ]
    )
    assert exit_code == 1
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert payload["pending_threshold_breached"] is True
    assert payload["replenishment_candidates"]
