from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.memory import memory


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_write_log_creates_entry_and_hash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(memory, "ROOT", tmp_path)
    monkeypatch.setattr(memory, "MEMORY_DIR", tmp_path / "memory")
    monkeypatch.setattr(memory, "LOG_PATH", tmp_path / "memory" / "log.jsonl")
    monkeypatch.setattr(memory, "STATE_PATH", tmp_path / "memory" / "state.json")
    monkeypatch.setattr(memory, "ARTIFACTS_PATH", tmp_path / "memory" / "artifacts.json")
    monkeypatch.setattr(memory, "RUNS_DIR", tmp_path / "memory" / "runs")

    payload = memory.write_log({"summary": "first"})
    assert "hash_self" in payload
    first_hash = payload["hash_self"]

    payload_2 = memory.write_log({"summary": "second"})
    assert payload_2["hash_prev"] == first_hash
    log_entries = _read_jsonl(memory.LOG_PATH)
    assert len(log_entries) == 2


def test_promote_fact_updates_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(memory, "ROOT", tmp_path)
    monkeypatch.setattr(memory, "MEMORY_DIR", tmp_path / "memory")
    monkeypatch.setattr(memory, "LOG_PATH", tmp_path / "memory" / "log.jsonl")
    monkeypatch.setattr(memory, "STATE_PATH", tmp_path / "memory" / "state.json")
    monkeypatch.setattr(memory, "ARTIFACTS_PATH", tmp_path / "memory" / "artifacts.json")
    monkeypatch.setattr(memory, "RUNS_DIR", tmp_path / "memory" / "runs")

    fact = {"id": "f1", "statement": "demo"}
    memory.promote_fact(fact)
    state = json.loads(memory.STATE_PATH.read_text(encoding="utf-8"))
    assert state["facts"][0]["statement"] == "demo"

    updated = {"id": "f1", "statement": "updated"}
    memory.promote_fact(updated)
    state = json.loads(memory.STATE_PATH.read_text(encoding="utf-8"))
    assert len(state["facts"]) == 1
    assert state["facts"][0]["statement"] == "updated"


def test_register_artifacts_deduplicates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(memory, "ROOT", tmp_path)
    monkeypatch.setattr(memory, "MEMORY_DIR", tmp_path / "memory")
    monkeypatch.setattr(memory, "LOG_PATH", tmp_path / "memory" / "log.jsonl")
    monkeypatch.setattr(memory, "STATE_PATH", tmp_path / "memory" / "state.json")
    monkeypatch.setattr(memory, "ARTIFACTS_PATH", tmp_path / "memory" / "artifacts.json")
    monkeypatch.setattr(memory, "RUNS_DIR", tmp_path / "memory" / "runs")

    memory.register_artifacts("task", [{"path": "a.txt", "sha256": "hash"}])
    memory.register_artifacts("task", [{"path": "b.txt", "sha256": "hash"}])
    index = json.loads(memory.ARTIFACTS_PATH.read_text(encoding="utf-8"))
    assert len(index["artifacts"]["task"]) == 1


def test_recall_returns_matches(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(memory, "ROOT", tmp_path)
    monkeypatch.setattr(memory, "MEMORY_DIR", tmp_path / "memory")
    monkeypatch.setattr(memory, "LOG_PATH", tmp_path / "memory" / "log.jsonl")
    monkeypatch.setattr(memory, "STATE_PATH", tmp_path / "memory" / "state.json")
    monkeypatch.setattr(memory, "ARTIFACTS_PATH", tmp_path / "memory" / "artifacts.json")
    monkeypatch.setattr(memory, "RUNS_DIR", tmp_path / "memory" / "runs")

    memory.write_log({"summary": "alpha run"})
    memory.write_log({"summary": "beta run"})
    memory.promote_fact({"id": "fact-alpha", "statement": "alpha fact"})
    result = memory.recall("alpha")
    assert result["log"]
    assert result["log"][0]["summary"] in {"alpha run", "beta run"}
    assert any("alpha" in fact["statement"] for fact in result["facts"])
