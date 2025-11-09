from __future__ import annotations

import json
from pathlib import Path

import teof.bootloader as bootloader
import teof._paths as paths
from tools.autonomy import hash_ledger


def _setup_repo(tmp_path: Path, monkeypatch) -> Path:
    # minimal repo markers for repo_root resolution
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    (tmp_path / "README.md").write_text("", encoding="utf-8")
    (tmp_path / "teof").mkdir()

    ledger_dir = tmp_path / "_report" / "usage" / "hash-ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(hash_ledger, "ROOT", tmp_path)
    monkeypatch.setattr(hash_ledger, "LEDGER_DIR", ledger_dir)
    monkeypatch.setattr(hash_ledger, "INDEX_FILE", ledger_dir / "index.jsonl")
    monkeypatch.setattr(hash_ledger, "STATE_FILE", ledger_dir / "state.json")
    monkeypatch.setattr(paths, "_ROOT_CACHE", tmp_path)
    return ledger_dir


def test_teof_hash_ledger_append_and_guard(monkeypatch, tmp_path: Path) -> None:
    ledger_dir = _setup_repo(tmp_path, monkeypatch)
    receipt_rel = "_report/usage/sample-receipt.json"
    receipt_path = tmp_path / receipt_rel
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps({"result": "ok"}), encoding="utf-8")

    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps({"systemic_targets": ["S1"]}), encoding="utf-8")

    exit_code = bootloader.main(
        [
            "hash_ledger",
            "append",
            "--plan",
            "2025-10-12-infinite-ledger",
            "--step",
            "S1",
            "--receipt",
            receipt_rel,
            "--agent",
            "codex-test",
            "--ts",
            "2025-11-09T19:00:00Z",
            "--metadata",
            str(metadata_path.relative_to(tmp_path)),
        ]
    )
    assert exit_code == 0

    entry_file = ledger_dir / "receipt-20251109T190000Z.json"
    assert entry_file.exists()
    payload = json.loads(entry_file.read_text(encoding="utf-8"))
    assert payload["plan_id"] == "2025-10-12-infinite-ledger"
    assert payload["plan_step_id"] == "S1"
    assert payload["receipt_path"] == receipt_rel
    assert payload["metadata"]["systemic_targets"] == ["S1"]

    guard_exit = bootloader.main(["hash_ledger", "guard"])
    assert guard_exit == 0
    state = json.loads((ledger_dir / "state.json").read_text(encoding="utf-8"))
    assert state["entry_count"] == 1
    assert len(state["tip_hash"]) == 64


def test_teof_hash_ledger_guard_detects_missing_receipt(monkeypatch, tmp_path: Path) -> None:
    ledger_dir = _setup_repo(tmp_path, monkeypatch)
    receipt_rel = "_report/usage/another-receipt.json"
    receipt_path = tmp_path / receipt_rel
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text("{}", encoding="utf-8")

    hash_ledger.append_entry(
        plan_id="2025-10-12-infinite-ledger",
        plan_step_id=None,
        receipt_path=receipt_rel,
        agent_id="codex-test",
        timestamp="2025-11-09T19:05:00Z",
    )

    # Remove receipt to force guard failure
    receipt_path.unlink()
    exit_code = bootloader.main(["hash_ledger", "guard"])
    assert exit_code == 2
    index_path = ledger_dir / "index.jsonl"
    assert index_path.exists()
