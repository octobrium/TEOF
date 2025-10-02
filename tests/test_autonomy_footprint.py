from __future__ import annotations

import json
from pathlib import Path

from teof.status_report import get_autonomy_footprint

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "docs" / "automation" / "autonomy-footprint-baseline.json"


def test_autonomy_footprint_matches_baseline() -> None:
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    footprint = get_autonomy_footprint(ROOT)
    assert footprint == baseline
