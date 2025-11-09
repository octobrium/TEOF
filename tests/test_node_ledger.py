from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.autonomy import node_ledger


def _setup_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ledger_dir = tmp_path / "ledger"
    monkeypatch.setattr(node_ledger, "LEDGER_DIR", ledger_dir)
    monkeypatch.setattr(node_ledger, "LEDGER_PATH", ledger_dir / "ledger.jsonl")
    monkeypatch.setattr(node_ledger, "LATEST_PATH", ledger_dir / "latest.json")
    monkeypatch.setattr(node_ledger, "ROOT", tmp_path)


def _create_artifact(tmp_path: Path, relative: str) -> str:
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("receipt", encoding="utf-8")
    return relative


def test_append_entry_generates_hash_chain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup_paths(tmp_path, monkeypatch)
    plan_path = _create_artifact(tmp_path, "_plans/sample.plan.json")
    proof_path = _create_artifact(tmp_path, "_report/agent/demo/receipt.json")

    first = node_ledger.append_entry(
        node_id="codex-7",
        action="grant",
        stake_delta=10,
        reputation_delta=0.1,
        authority=plan_path,
        proofs=[proof_path],
        notes="bootstrap",
        timestamp="2025-11-09T05:00:00Z",
    )
    second = node_ledger.append_entry(
        node_id="codex-7",
        action="reward",
        stake_delta=5,
        reputation_delta=0.05,
        authority=plan_path,
        proofs=[proof_path],
        notes=None,
        timestamp="2025-11-09T05:01:00Z",
    )

    assert first["hash_prev"] == ""
    assert second["hash_prev"] == first["hash_self"]
    assert node_ledger.LATEST_PATH.exists()


def test_show_entries_prints_table(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup_paths(tmp_path, monkeypatch)
    plan_path = _create_artifact(tmp_path, "_plans/sample.plan.json")
    proof_path = _create_artifact(tmp_path, "_report/agent/demo/receipt.json")
    node_ledger.append_entry(
        node_id="codex-9",
        action="grant",
        stake_delta=1,
        reputation_delta=0.01,
        authority=plan_path,
        proofs=[proof_path],
        notes=None,
        timestamp="2025-11-09T05:10:00Z",
    )

    node_ledger.show_entries(node_id="codex-9", limit=5)
    output = capsys.readouterr().out
    assert "codex-9" in output
    assert "grant" in output


def test_audit_detects_tampering(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup_paths(tmp_path, monkeypatch)
    plan_path = _create_artifact(tmp_path, "_plans/sample.plan.json")
    proof_path = _create_artifact(tmp_path, "_report/agent/demo/receipt.json")
    node_ledger.append_entry(
        node_id="codex-9",
        action="grant",
        stake_delta=1,
        reputation_delta=0.01,
        authority=plan_path,
        proofs=[proof_path],
        notes=None,
        timestamp="2025-11-09T05:10:00Z",
    )

    # Corrupt the ledger file
    contents = node_ledger.LEDGER_PATH.read_text(encoding="utf-8").strip().splitlines()
    payload = json.loads(contents[0])
    payload["stake_delta"] = 999
    node_ledger.LEDGER_PATH.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        node_ledger.audit_entries()
