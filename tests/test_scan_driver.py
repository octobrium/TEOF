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
    monkeypatch.setattr(scan_driver, "DEFAULT_POLICY_PATH", root / "scan-policy.json", raising=False)
    monkeypatch.setattr(scan_driver.session_guard, "ensure_recent_session", lambda *a, **k: None)

    base_report = scan_driver.parallel_guard.ParallelReport(
        agent_id="codex-test",
        severity="none",
        generated_at="2025-10-05T00:00:00Z",
        config={},
    )
    base_report.requirements = {
        "session_boot": False,
        "plan_claim": False,
        "post_run_scan": False,
    }
    monkeypatch.setattr(
        scan_driver.parallel_guard,
        "detect_parallel_state",
        lambda agent_id, *, now=None: base_report,
    )
    monkeypatch.setattr(
        scan_driver.parallel_guard,
        "format_summary",
        lambda report: "Parallel state: none",
    )
    monkeypatch.setattr(
        scan_driver.parallel_guard,
        "write_parallel_receipt",
        lambda agent_id, report: root / "parallel.json",
    )

    # Seed default files
    (root / "_plans" / "next-development.todo.json").write_text(json.dumps({"items": []}) + "\n", encoding="utf-8")
    (root / "agents" / "tasks" / "tasks.json").write_text(json.dumps({"tasks": []}) + "\n", encoding="utf-8")
    (root / "memory" / "state.json").write_text(json.dumps({"facts": []}) + "\n", encoding="utf-8")

    policy = {
        "version": 1,
        "tracked_inputs": {
            "backlog": {"path": "_plans/next-development.todo.json"},
            "tasks": {"path": "agents/tasks/tasks.json"},
            "state": {"path": "memory/state.json"},
        },
        "components": {
            "frontier": {"triggers": ["backlog", "tasks"]},
            "critic": {"triggers": ["backlog", "state"]},
            "tms": {"triggers": ["state"]},
            "ethics": {"triggers": ["backlog", "tasks"]},
        },
        "cache": {"reuse_window_seconds": 0, "reuse_requires_summary": True},
    }
    (root / "scan-policy.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")


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

    exit_code = scan_driver.main(["--dry-run", "--policy", str(scan_driver.DEFAULT_POLICY_PATH)])
    assert exit_code == 0

    output = capsys.readouterr().out
    assert "Parallel state: none" in output
    assert "scan_driver: would run frontier, critic, tms, ethics" in output

    history_entries = _read_history(scan_driver.HISTORY_PATH)
    assert history_entries[-1]["components"] == ["frontier", "critic", "tms", "ethics"]
    assert history_entries[-1]["dry_run"] is True
    assert "parallel" in history_entries[-1]


def test_detects_state_change_and_runs_subset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup_repo(tmp_path, monkeypatch)

    # Record baseline inputs
    policy = scan_driver.load_policy(scan_driver.DEFAULT_POLICY_PATH)
    baseline = scan_driver._current_inputs(policy.tracked_inputs)
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

    exit_code = scan_driver.main(["--policy", str(scan_driver.DEFAULT_POLICY_PATH)])
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
    assert "parallel" in last_entry


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
            "--policy",
            str(scan_driver.DEFAULT_POLICY_PATH),
        ]
    )
    assert exit_code == 0
    assert not recorded_calls

    output = capsys.readouterr().out
    assert "Parallel state: none" in output
    assert "scan_driver: no components selected" in output

    history_entries = _read_history(scan_driver.HISTORY_PATH)
    assert history_entries[-1]["components"] == []
    assert "parallel" in history_entries[-1]
