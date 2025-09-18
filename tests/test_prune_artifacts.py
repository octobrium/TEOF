from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tools.maintenance.prune_artifacts import discover_moves, prune_artifacts


@pytest.fixture()
def demo_root(tmp_path: Path) -> Path:
    plans = tmp_path / "_plans"
    plans.mkdir()
    report = tmp_path / "_report" / "agent" / "codex-9" / "demo-task"
    report.mkdir(parents=True)
    (report / "notes.md").write_text("demo", encoding="utf-8")
    (tmp_path / "_report" / "agent" / "codex-9" / "recent.md").write_text("recent", encoding="utf-8")
    (plans / "2025-09-18-prune-script.plan.json").write_text("{}", encoding="utf-8")
    (plans / "README.md").write_text("keep", encoding="utf-8")
    return tmp_path


def _set_mtime(path: Path, hours_ago: float) -> None:
    ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).timestamp()
    os.utime(path, (ts, ts))


def test_discover_moves_respects_cutoff(demo_root: Path) -> None:
    plan = demo_root / "_plans" / "2025-09-18-prune-script.plan.json"
    stale_dir = demo_root / "_report" / "agent" / "codex-9" / "demo-task"
    recent = demo_root / "_report" / "agent" / "codex-9" / "recent.md"

    _set_mtime(plan, hours_ago=200)
    _set_mtime(stale_dir, hours_ago=200)
    _set_mtime(stale_dir / "notes.md", hours_ago=200)
    _set_mtime(recent, hours_ago=5)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
    moves = discover_moves(demo_root, ["_plans", "_report/agent"], cutoff, "20250101T000000Z")
    relative_sources = {m.source.relative_to(demo_root) for m in moves}

    assert Path("_plans/2025-09-18-prune-script.plan.json") in relative_sources
    assert Path("_report/agent/codex-9/demo-task") in relative_sources
    assert Path("_report/agent/codex-9/recent.md") not in relative_sources
    assert Path("_plans/README.md") not in relative_sources


def test_prune_artifacts_moves_when_not_dry(demo_root: Path) -> None:
    plan = demo_root / "_plans" / "2025-09-18-prune-script.plan.json"
    stale_dir = demo_root / "_report" / "agent" / "codex-9" / "demo-task"

    _set_mtime(plan, hours_ago=150)
    _set_mtime(stale_dir, hours_ago=150)
    _set_mtime(stale_dir / "notes.md", hours_ago=150)

    stamp = "20250101T000000Z"
    moves = prune_artifacts(
        root=demo_root,
        targets=["_plans", "_report/agent"],
        cutoff_hours=72,
        dry_run=False,
        stamp=stamp,
    )

    apoptosis_plan = demo_root / "_apoptosis" / stamp / "_plans" / "2025-09-18-prune-script.plan.json"
    apoptosis_task_dir = demo_root / "_apoptosis" / stamp / "_report" / "agent" / "codex-9" / "demo-task"

    assert apoptosis_plan.exists()
    assert apoptosis_task_dir.exists()
    assert (apoptosis_task_dir / "notes.md").exists()
    assert not plan.exists()
    assert not stale_dir.exists()
    assert len(moves) == 2
