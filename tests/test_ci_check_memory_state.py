from __future__ import annotations

import json
from importlib import reload
from pathlib import Path

import pytest

import scripts.ci.check_memory_state as check_memory_state


@pytest.fixture()
def tmp_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path
    memory_dir = root / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)

    # Patch paths in module to point at the temp repo
    monkeypatch.setattr(check_memory_state, "ROOT", root)
    monkeypatch.setattr(check_memory_state, "STATE_PATH", memory_dir / "state.json")
    monkeypatch.setattr(check_memory_state, "LOG_PATH", memory_dir / "log.jsonl")
    reload(check_memory_state)
    monkeypatch.setattr(check_memory_state, "ROOT", root)
    monkeypatch.setattr(check_memory_state, "STATE_PATH", memory_dir / "state.json")
    monkeypatch.setattr(check_memory_state, "LOG_PATH", memory_dir / "log.jsonl")

    return root


def write_state(path: Path, facts: list[dict]) -> None:
    payload = {"facts": facts, "version": 0}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_log(path: Path, entries: list[dict]) -> None:
    text = "\n".join(json.dumps(entry, sort_keys=True) for entry in entries)
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def test_check_memory_state_passes_with_receipt(tmp_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # base state/log empty
    monkeypatch.setenv("BASE_SHA", "BASE")
    monkeypatch.setattr(check_memory_state, "_git_show", lambda path, base: [])

    head_state = check_memory_state.STATE_PATH
    head_log = check_memory_state.LOG_PATH

    write_state(head_state, [
        {
            "id": "fact-1",
            "statement": "New fact",
            "source_run": "20250926T200000Z-abc123",
        }
    ])
    write_log(head_log, [
        {
            "ts": "2025-09-26T20:00:00Z",
            "summary": "Promoted fact",
            "run_id": "20250926T200000Z-abc123",
            "hash_prev": None,
            "hash_self": "0" * 64,
            "derived_facts": ["fact-1"],
        }
    ])

    assert check_memory_state.main() == 0


def test_check_memory_state_flags_missing_receipt(tmp_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("BASE_SHA", "BASE")
    monkeypatch.setattr(check_memory_state, "_git_show", lambda path, base: [])

    head_state = check_memory_state.STATE_PATH
    head_log = check_memory_state.LOG_PATH

    write_state(head_state, [
        {
            "id": "fact-1",
            "statement": "New fact",
            "source_run": "20250926T200000Z-abc123",
        }
    ])
    # Log entry without matching run_id/derived_facts
    write_log(head_log, [
        {
            "ts": "2025-09-26T20:00:00Z",
            "summary": "Promoted fact",
            "run_id": "different",
            "hash_prev": None,
            "hash_self": "0" * 64,
            "derived_facts": [],
        }
    ])

    rc = check_memory_state.main()
    out = capsys.readouterr().out
    assert rc == 1
    assert "Fact 'fact-1'" in out

