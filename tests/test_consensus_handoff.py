from __future__ import annotations

import json
from pathlib import Path

from tools.automation import consensus_handoff


def test_handoff_writes_receipt_and_pointer(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "repo"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(consensus_handoff, "ROOT", root)
    handoff_dir = root / "_report" / "analysis" / "consensus-handoff"
    args = [
        "--pending-action",
        "Push feature/consensus",
        "--reason",
        "No bus access",
        "--agent-id",
        "codex-5",
        "--plan-id",
        "2025-11-09-autonomy-module-consolidation",
        "--branch",
        "feature/consensus",
        "--details",
        "Need reviewer to bus-approve + push",
        "--requires-push",
    ]
    rc = consensus_handoff.main(args)
    assert rc == 0
    receipts = sorted(handoff_dir.glob("handoff-*.json"))
    assert receipts
    payload = json.loads(receipts[0].read_text(encoding="utf-8"))
    assert payload["pending_action"] == "Push feature/consensus"
    pointer = json.loads((handoff_dir / "latest.json").read_text(encoding="utf-8"))
    assert pointer["requires_push"] is True
    assert pointer["receipt"].endswith(".json")
