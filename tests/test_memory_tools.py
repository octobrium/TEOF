import json
import importlib.util
import sys
from pathlib import Path

from tools.memory import memory as memory_mod


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _patch_memory_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(memory_mod, "ROOT", tmp_path)
    monkeypatch.setattr(memory_mod, "MEMORY_DIR", tmp_path / "memory")
    monkeypatch.setattr(memory_mod, "LOG_PATH", tmp_path / "memory" / "log.jsonl")
    monkeypatch.setattr(memory_mod, "STATE_PATH", tmp_path / "memory" / "state.json")
    monkeypatch.setattr(memory_mod, "ARTIFACTS_PATH", tmp_path / "memory" / "artifacts.json")
    monkeypatch.setattr(memory_mod, "RUNS_DIR", tmp_path / "memory" / "runs")


def write_log(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            json.dump(entry, handle)
            handle.write("\n")


def test_log_entry_appends(monkeypatch, tmp_path, capsys):
    module = load_module("memory_log_entry", "tools/memory/log-entry.py")
    _patch_memory_paths(tmp_path, monkeypatch)
    log_path = memory_mod.LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(module, "default_actor", lambda: "tester")
    monkeypatch.setattr(sys, "argv", [
        "memory-log-entry",
        "--summary",
        "Added receipt",
        "--ref",
        "feature/123",
        "--artifact",
        "_report/demo.txt",
        "--signature",
        "sig-1",
        "--receipt",
        "_report/demo.txt",
        "--task",
        "task-1",
        "--layer",
        "L5",
        "--systemic-scale",
        "4",
    ])

    module.main()
    output = capsys.readouterr().out
    assert "Appended memory entry" in output
    assert "run_id=" in output

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["summary"] == "Added receipt"
    assert record["ref"] == "feature/123"
    assert record["artifacts"] == ["_report/demo.txt"]
    assert record["signatures"] == ["sig-1"]
    assert record["receipts"] == ["_report/demo.txt"]
    assert record["actor"] == "tester"
    assert record["task"] == "task-1"
    assert record["layer"] == "L5"
    assert record["systemic_scale"] == 4
    assert isinstance(record["run_id"], str) and record["run_id"]
    assert isinstance(record["hash_self"], str) and len(record["hash_self"]) == 64


def test_query_filters_by_actor(monkeypatch, tmp_path, capsys):
    module = load_module("memory_query", "tools/memory/query.py")
    log_path = tmp_path / "log.jsonl"
    write_log(
        log_path,
        [
            {
                "ts": "2025-09-20T10:00:00Z",
                "actor": "alice",
                "summary": "Alpha",
                "ref": "feat/a",
                "artifacts": [],
                "signatures": [],
            },
            {
                "ts": "2025-09-20T11:00:00Z",
                "actor": "bob",
                "summary": "Beta",
                "ref": "feat/b",
                "artifacts": [],
                "signatures": [],
            },
        ],
    )

    monkeypatch.setattr(module, "LOG_PATH", log_path)
    monkeypatch.setattr(sys, "argv", [
        "memory-query",
        "--limit",
        "1",
        "--actor",
        "alice",
    ])

    module.main()
    output = capsys.readouterr().out
    assert "Alpha" in output
    assert "Beta" not in output


def test_hot_index_build_and_query(monkeypatch, tmp_path, capsys):
    module = load_module("memory_hot_index", "tools/memory/hot_index.py")
    log_path = tmp_path / "log.jsonl"
    index_path = tmp_path / "hot_index.json"

    entries = [
        {
            "ts": "2025-09-20T12:00:00Z",
            "actor": "alice",
            "summary": "Gamma",
            "ref": "feat/c",
            "artifacts": ["a"],
            "signatures": ["sig"],
        },
        {
            "ts": "2025-09-20T13:00:00Z",
            "actor": "carol",
            "summary": "Delta",
            "ref": "feat/d",
            "artifacts": [],
            "signatures": [],
        },
    ]
    write_log(log_path, entries)

    monkeypatch.setattr(module, "LOG_PATH", log_path)
    monkeypatch.setattr(module, "INDEX_PATH", index_path)
    monkeypatch.setattr(module, "ROOT", tmp_path)

    monkeypatch.setattr(sys, "argv", ["hot-index", "build", "--limit", "2"])
    assert module.main() == 0
    capsys.readouterr()
    idx = json.loads(index_path.read_text(encoding="utf-8"))
    assert len(idx) == 2
    assert {entry["summary"] for entry in idx} == {"Gamma", "Delta"}

    monkeypatch.setattr(sys, "argv", [
        "hot-index",
        "query",
        "--use-index",
        "--json",
        "--actor",
        "alice",
    ])
    assert module.main() == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert len(payload) == 1
    assert payload[0]["summary"] == "Gamma"
