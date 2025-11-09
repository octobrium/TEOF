from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from tools.autonomy import hash_ledger


def _setup_env(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path
    ledger_dir = root / "_report" / "usage" / "hash-ledger"
    monkeypatch.setattr(hash_ledger, "ROOT", root)
    monkeypatch.setattr(hash_ledger, "LEDGER_DIR", ledger_dir)
    monkeypatch.setattr(hash_ledger, "INDEX_FILE", ledger_dir / "index.jsonl")
    monkeypatch.setattr(hash_ledger, "STATE_FILE", ledger_dir / "state.json")


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_append_entry_creates_receipt(tmp_path, monkeypatch):
    _setup_env(monkeypatch, tmp_path)
    receipt_dir = tmp_path / "_report" / "usage" / "plan-scope"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    target_receipt = receipt_dir / "sample.json"
    target_receipt.write_text("{}", encoding="utf-8")

    entry_path, payload = hash_ledger.append_entry(
        plan_id="2025-10-12-infinite-ledger",
        plan_step_id="S1",
        receipt_path=target_receipt,
        agent_id="codex-tier2",
        timestamp=_iso_now(),
        metadata={"note": "test"},
    )

    assert entry_path.exists()
    stored = json.loads(entry_path.read_text())
    assert stored["plan_id"] == "2025-10-12-infinite-ledger"
    assert stored["prev_hash"] == "0" * 64
    assert stored["metadata"] == {"note": "test"}
    state = json.loads((hash_ledger.STATE_FILE).read_text())
    assert state["entry_count"] == 1
    assert state["tip_hash"] == stored["hash"] == payload["hash"]


def test_guard_detects_missing_receipt(tmp_path, monkeypatch):
    _setup_env(monkeypatch, tmp_path)
    receipts = tmp_path / "_report" / "usage" / "plan-scope"
    receipts.mkdir(parents=True, exist_ok=True)
    first_receipt = receipts / "one.json"
    first_receipt.write_text("{}", encoding="utf-8")
    hash_ledger.append_entry(
        plan_id="plan-a",
        plan_step_id=None,
        receipt_path=first_receipt,
        agent_id="codex-tier2",
        timestamp=_iso_now(),
        metadata={"idx": 1},
    )
    missing_receipt = receipts / "two.json"
    hash_ledger.append_entry(
        plan_id="plan-a",
        plan_step_id=None,
        receipt_path=missing_receipt,
        agent_id="codex-tier2",
        timestamp=_iso_now(),
        metadata={"idx": 2},
    )
    # intentionally remove the second receipt to trigger guard failure
    if missing_receipt.exists():
        missing_receipt.unlink()

    ok, issues, total = hash_ledger.guard_ledger()

    assert not ok
    assert total == 2
    assert any("missing receipt" in issue for issue in issues)
