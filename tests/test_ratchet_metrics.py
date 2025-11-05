import datetime as dt
import json
from pathlib import Path

import pytest

from tools.metrics import ratchet


@pytest.fixture()
def repo_root(tmp_path: Path) -> Path:
    (tmp_path / "_plans").mkdir()
    (tmp_path / "_bus" / "claims").mkdir(parents=True)
    return tmp_path


def write_plan(root: Path, name: str, data: dict) -> None:
    path = root / "_plans" / f"{name}.plan.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_claim(root: Path, name: str, data: dict) -> None:
    path = root / "_bus" / "claims" / f"{name}.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_compute_snapshot_basic(repo_root: Path) -> None:
    write_plan(
        repo_root,
        "done-plan",
        {
            "plan_id": "done-plan",
            "created": "2025-01-01T00:00:00Z",
            "status": "done",
            "steps": [
                {"id": "S1", "status": "done"},
                {"id": "S2", "status": "done"},
            ],
            "checkpoint": {"status": "satisfied"},
        },
    )
    write_plan(
        repo_root,
        "active-plan",
        {
            "plan_id": "active-plan",
            "created": "2025-01-05T00:00:00Z",
            "status": "in_progress",
            "steps": [
                {"id": "S1", "status": "done"},
                {"id": "S2", "status": "queued"},
            ],
            "checkpoint": {"status": "pending"},
        },
    )

    write_claim(
        repo_root,
        "QUEUE-001",
        {
            "task_id": "QUEUE-001",
            "status": "active",
            "claimed_at": "2025-01-06T00:00:00Z",
        },
    )
    write_claim(
        repo_root,
        "QUEUE-002",
        {
            "task_id": "QUEUE-002",
            "status": "done",
            "claimed_at": "2025-01-02T00:00:00Z",
            "released_at": "2025-01-04T00:00:00Z",
        },
    )

    now = dt.datetime(2025, 1, 10, 12, 0, 0, tzinfo=dt.timezone.utc)
    counts = {"frontier": 2, "critic": 1, "tms": 0, "ethics": 0}
    snapshot = ratchet.compute_snapshot(
        root=repo_root,
        now=now,
        scan_counts=counts,
        frontier_entries=[{"id": 1}, {"id": 2}],
        critic_anomalies=[{"id": "crit-1"}],
        tms_conflicts=[],
        ethics_violations=[],
    )

    assert snapshot.coherence_gain == pytest.approx(5.0)
    assert snapshot.complexity_added == pytest.approx(5.0)
    assert snapshot.closure_velocity == pytest.approx(1.0)
    assert snapshot.risk_load == pytest.approx(1.0)
    assert snapshot.ratchet_index == pytest.approx(1.0)

    assert snapshot.plan_stats.total_plans == 2
    assert snapshot.plan_stats.done_plans == 1
    assert snapshot.plan_stats.active_plans == 1
    assert snapshot.plan_stats.closed_steps == 3
    assert snapshot.plan_stats.open_steps == 1
    assert snapshot.plan_stats.checkpoint_satisfied == 1
    assert snapshot.plan_stats.median_age_days > 0

    assert snapshot.claim_stats.total_claims == 2
    assert snapshot.claim_stats.active_claims == 1
    assert snapshot.claim_stats.terminal_claims == 1


def test_write_snapshot_creates_history(repo_root: Path) -> None:
    now = dt.datetime(2025, 1, 10, 12, 0, 0, tzinfo=dt.timezone.utc)
    snapshot = ratchet.compute_snapshot(
        root=repo_root,
        now=now,
        scan_counts={"frontier": 0, "critic": 0, "tms": 0, "ethics": 0},
        frontier_entries=[],
        critic_anomalies=[],
        tms_conflicts=[],
        ethics_violations=[],
    )

    out_dir = repo_root / "_report" / "usage" / "systemic_out"
    path = ratchet.write_snapshot(snapshot, root=repo_root, out_dir=out_dir)

    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["ratchet_index"] == snapshot.ratchet_index

    history_path = repo_root / ratchet.HISTORY_DIR / "ratchet-history.jsonl"
    assert history_path.exists()
    lines = history_path.read_text(encoding="utf-8").strip().splitlines()
    assert lines
    history_payload = json.loads(lines[-1])
    assert history_payload["stamp"] == payload["stamp"]
