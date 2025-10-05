from __future__ import annotations

import json
from pathlib import Path
from typing import List

import pytest

from tools.autonomy import scan_driver


def _setup_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path
    for relative in ("_plans", "agents/tasks", "memory", "_report/usage"):
        (root / relative).mkdir(parents=True, exist_ok=True)

    # Point driver globals at the temporary repository
    monkeypatch.setattr(scan_driver, "ROOT", root, raising=False)
    monkeypatch.setattr(scan_driver, "HISTORY_PATH", root / "_report" / "usage" / "scan-history.jsonl", raising=False)
    monkeypatch.setattr(
        scan_driver,
        "TRACKED_INPUTS",
        {
            "backlog": root / "_plans" / "next-development.todo.json",
            "tasks": root / "agents" / "tasks" / "tasks.json",
            "state": root / "memory" / "state.json",
        },
        raising=False,
    )

    # Seed default files
    (root / "_plans" / "next-development.todo.json").write_text(json.dumps({"items": []}) + "\n", encoding="utf-8")
    (root / "agents" / "tasks" / "tasks.json").write_text(json.dumps({"tasks": []}) + "\n", encoding="utf-8")
    (root / "memory" / "state.json").write_text(json.dumps({"facts": []}) + "\n", encoding="utf-8")


def _read_history(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries: List[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def test_dry_run_lists_components(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup_repo(tmp_path, monkeypatch)

    exit_code = scan_driver.main(["--dry-run"])
    assert exit_code == 0

    output = capsys.readouterr().out
    assert "scan_driver: would run frontier, critic, tms, ethics" in output

    history_entries = _read_history(scan_driver.HISTORY_PATH)
    assert history_entries[-1]["components"] == ["frontier", "critic", "tms", "ethics"]
    assert history_entries[-1]["dry_run"] is True


def test_detects_state_change_and_runs_subset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup_repo(tmp_path, monkeypatch)

    # Record baseline inputs
    baseline = scan_driver._current_inputs()
    entry = {
        "generated_at": "baseline",
        "components": ["frontier", "critic", "tms", "ethics"],
        "inputs": baseline,
    }
    scan_driver._write_history(scan_driver.HISTORY_PATH, entry)

    # Update state.json to trigger critic + tms
    (tmp_path / "memory" / "state.json").write_text(json.dumps({"facts": [{"id": "f1"}]}) + "\n", encoding="utf-8")

    recorded_args: list[list[str]] = []

    def fake_main(argv: list[str]) -> int:
        recorded_args.append(argv)
        return 0

    monkeypatch.setattr(scan_driver.bootloader, "main", fake_main)

    exit_code = scan_driver.main([])
    assert exit_code == 0
    assert recorded_args
    scan_args = recorded_args[0]
    assert scan_args.count("--only") == 2
    assert scan_args[-4:] == ["--only", "critic", "--only", "tms"] or scan_args[-4:] == ["--only", "tms", "--only", "critic"]

    history_entries = _read_history(scan_driver.HISTORY_PATH)
    last_entry = history_entries[-1]
    assert last_entry["components"] == ["critic", "tms"]
    assert last_entry["reasons"]["critic"] == ["state"]
    assert last_entry["reasons"]["tms"] == ["state"]


def test_skip_all_results_in_noop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup_repo(tmp_path, monkeypatch)

    recorded_calls: list[list[str]] = []

    def fake_main(argv: list[str]) -> int:
        recorded_calls.append(argv)
        return 0

    monkeypatch.setattr(scan_driver.bootloader, "main", fake_main)

    exit_code = scan_driver.main(
        [
            "--skip",
            "frontier",
            "--skip",
            "critic",
            "--skip",
            "tms",
            "--skip",
            "ethics",
        ]
    )
    assert exit_code == 0
    assert not recorded_calls

    output = capsys.readouterr().out
    assert "scan_driver: no components selected" in output

    history_entries = _read_history(scan_driver.HISTORY_PATH)
    assert history_entries[-1]["components"] == []
