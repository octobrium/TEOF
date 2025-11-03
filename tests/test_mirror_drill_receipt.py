from __future__ import annotations

import json
from pathlib import Path

from tools.onboarding import mirror_drill


def test_mirror_drill_receipt(tmp_path: Path, monkeypatch) -> None:
    out_dir = tmp_path / "_report" / "usage" / "mirror-drill"
    monkeypatch.setattr(mirror_drill, "DEFAULT_RECEIPT_DIR", out_dir)
    args = [
        "--agent",
        "observer-h",
        "--medium",
        "human",
        "--plan-id",
        "PLAN-001",
        "--systemic-targets",
        "s1",
        "s2",
        "--layer-targets",
        "l4",
        "l5",
        "--summary",
        "Validated cross substrate replay",
        "--artifacts",
        "_report/usage/autonomy-preflight/preflight-20250101.json",
        "--risks",
        "handoff-gap",
    ]
    exit_code = mirror_drill.main(args)
    assert exit_code == 0
    receipts = list(out_dir.glob("mirror-*.json"))
    assert len(receipts) == 1
    payload = json.loads(receipts[0].read_text(encoding="utf-8"))
    assert payload["agent"] == "observer-h"
    assert payload["systemic_targets"] == ["S1", "S2"]
    assert payload["layer_targets"] == ["L4", "L5"]
    assert payload["artifacts"] == ["_report/usage/autonomy-preflight/preflight-20250101.json"]
