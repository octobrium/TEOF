from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tools.autonomy.actions import hygiene


def _set_mtime(path: Path, *, hours_ago: float) -> None:
    ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).timestamp()
    os.utime(path, (ts, ts))


@pytest.fixture()
def hygiene_root(tmp_path: Path) -> Path:
    chronicle = tmp_path / "_report" / "usage" / "chronicle"
    chronicle.mkdir(parents=True)
    for idx in range(3):
        file = chronicle / f"chronicle-{idx}.json"
        file.write_text("{}", encoding="utf-8")
        _set_mtime(file, hours_ago=100 + idx)

    selfprompt = tmp_path / "_report" / "usage" / "selfprompt"
    selfprompt.mkdir(parents=True)
    for idx in range(2):
        file = selfprompt / f"selfprompt-{idx}.json"
        file.write_text("{}", encoding="utf-8")
        _set_mtime(file, hours_ago=90 + idx)

    plan = tmp_path / "_plans" / "2025-09-20-demo.plan.json"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("{}", encoding="utf-8")
    _set_mtime(plan, hours_ago=80)

    return tmp_path


def test_hygiene_reports_prune_and_rotation(hygiene_root: Path) -> None:
    payload = hygiene.run(
        root=hygiene_root,
        dry_run=True,
        keep_chronicle=1,
        keep_selfprompt=1,
        prune_cutoff_hours=24.0,
        prune_targets=("_plans",),
    )

    result = payload["result"]
    actions = result["actions"]

    assert len(actions["chronicle_rotation"]["removed"]) == 2
    assert len(actions["selfprompt_rotation"]["removed"]) == 1

    prune = actions["prune"]
    assert prune["cutoff_hours"] == 24.0
    assert prune["targets"] == ["_plans"]
    assert prune["moves"]
    assert not prune["executed"]

    plan = hygiene_root / "_plans" / "2025-09-20-demo.plan.json"
    assert plan.exists()

    payload_apply = hygiene.run(
        root=hygiene_root,
        dry_run=False,
        keep_chronicle=1,
        keep_selfprompt=1,
        prune_cutoff_hours=24.0,
        prune_targets=("_plans",),
    )

    prune_apply = payload_apply["result"]["actions"]["prune"]
    assert prune_apply["executed"]
    stamp = prune_apply["stamp"]
    apoptosis_plan = hygiene_root / "_apoptosis" / stamp / "_plans" / "2025-09-20-demo.plan.json"
    assert apoptosis_plan.exists()
    assert not plan.exists()

    chronicle_files = sorted((hygiene_root / "_report" / "usage" / "chronicle").glob("*.json"))
    assert len(chronicle_files) == 1

