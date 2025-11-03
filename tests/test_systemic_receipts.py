from __future__ import annotations

import os
from pathlib import Path

from teof.eval import systemic_receipts


def test_receipt_evaluator_rewards_existing_receipts(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    receipt_dir = root / "_report" / "usage"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = receipt_dir / "sample.json"
    receipt_path.write_text(
        """{
  "receipt_sha256": "abc123",
  "systemic": {"verdict": "ready"},
  "risk": "low",
  "recovery": "manual",
  "verdict": "ready"
}
""",
        encoding="utf-8",
    )
    text = """
Task: Mirror drill
Receipts: _report/usage/sample.json
"""
    monkeypatch.setenv("TEOF_RECEIPT_ROOT", str(root))
    scores = systemic_receipts.evaluate(text)
    assert scores["structure"] == 1.0
    assert scores["alignment"] == 2.0
    assert scores["verification"] == 2.0
    assert scores["risk"] == 1.0
    assert scores["recovery"] == 1.0
    monkeypatch.delenv("TEOF_RECEIPT_ROOT", raising=False)


def test_receipt_evaluator_handles_missing_receipts(monkeypatch) -> None:
    monkeypatch.setenv("TEOF_RECEIPT_ROOT", os.getcwd())
    text = "Receipts: _report/usage/missing.json"
    scores = systemic_receipts.evaluate(text)
    assert scores["structure"] == 1.0
    for pillar in ("alignment", "verification", "risk", "recovery"):
        assert scores[pillar] == 0.0
    monkeypatch.delenv("TEOF_RECEIPT_ROOT", raising=False)
