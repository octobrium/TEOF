from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.memory import cli, memory


def _patch_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(memory, "ROOT", tmp_path)
    monkeypatch.setattr(memory, "MEMORY_DIR", tmp_path / "memory")
    monkeypatch.setattr(memory, "LOG_PATH", tmp_path / "memory" / "log.jsonl")
    monkeypatch.setattr(memory, "STATE_PATH", tmp_path / "memory" / "state.json")
    monkeypatch.setattr(memory, "ARTIFACTS_PATH", tmp_path / "memory" / "artifacts.json")
    monkeypatch.setattr(memory, "RUNS_DIR", tmp_path / "memory" / "runs")


def _write_run(summary: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    payload = memory.write_log(
        {"summary": summary},
        capsule={"summary": summary},
    )
    return payload["run_id"]


def test_doctor_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_paths(tmp_path, monkeypatch)
    _write_run("first", tmp_path, monkeypatch)
    _write_run("second", tmp_path, monkeypatch)

    parser = cli.build_parser()
    args = parser.parse_args(["doctor"])
    rc = args.func(args)
    assert rc == 0


def test_doctor_detects_hash_break(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_paths(tmp_path, monkeypatch)
    _write_run("first", tmp_path, monkeypatch)
    log_path = memory.LOG_PATH
    lines = log_path.read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0])
    first["summary"] = "tampered"
    lines[0] = json.dumps(first)
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    parser = cli.build_parser()
    args = parser.parse_args(["doctor"])
    rc = args.func(args)
    assert rc == 1


def test_timeline_filters(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _patch_paths(tmp_path, monkeypatch)
    memory.write_log({"summary": "alpha", "task": "A"})
    memory.write_log({"summary": "beta", "task": "B"})

    parser = cli.build_parser()
    args = parser.parse_args(["timeline", "--task", "A", "--limit", "5"])
    args.func(args)
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" not in out


def test_diff_outputs_difference(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _patch_paths(tmp_path, monkeypatch)
    run1 = memory.write_log({"summary": "alpha"}, capsule={})
    run2 = memory.write_log({"summary": "beta"}, capsule={})

    parser = cli.build_parser()
    args = parser.parse_args(["diff", "--run", run2["run_id"], "--against", run1["run_id"]])
    args.func(args)
    out = capsys.readouterr().out
    assert "summary" in out
    assert "beta" in out
    assert "alpha" in out
