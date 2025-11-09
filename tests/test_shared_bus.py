from __future__ import annotations

import json
from pathlib import Path

from tools.autonomy import shared_bus


def test_emit_claim_writes_payload(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "repo"
    (root / "_bus").mkdir(parents=True, exist_ok=True)
    receipt = root / "receipts" / "demo.json"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(shared_bus, "ROOT", root)
    claim_path = shared_bus.emit_claim(
        "REPAIR-DEMO",
        agent_id="critic",
        note="Fix missing receipt",
        plan_id="demo-plan",
        receipt_path=receipt,
    )
    payload = json.loads(claim_path.read_text(encoding="utf-8"))
    assert payload["task_id"] == "REPAIR-DEMO"
    assert payload["agent_id"] == "critic"
    assert payload["branch"] == "agent/critic/repair-demo"
    assert payload["receipt"] == "receipts/demo.json"


def test_emit_claim_idempotent(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "repo"
    (root / "_bus").mkdir(parents=True, exist_ok=True)
    receipt = root / "r.json"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(shared_bus, "ROOT", root)
    first = shared_bus.emit_claim(
        "ETHICS-123",
        agent_id="ethics_gate",
        note=None,
        plan_id="123",
        receipt_path=receipt,
        branch="agent/ethics/ethics-123",
    )
    second = shared_bus.emit_claim(
        "ETHICS-123",
        agent_id="ethics_gate",
        note="ignored",
        plan_id="other",
        receipt_path=receipt,
        branch="agent/ethics/ethics-123",
    )
    assert first == second
