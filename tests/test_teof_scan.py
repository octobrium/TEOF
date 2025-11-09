from __future__ import annotations

import json
from pathlib import Path

import pytest

import teof.bootloader as bootloader


def _setup_scan_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path
    # Ensure expected directories exist
    for relative in ("_bus/claims", "_plans", "memory", "agents/tasks"):
        (root / relative).mkdir(parents=True, exist_ok=True)

    # Point bootloader and autonomy modules at the temporary repo
    monkeypatch.setattr(bootloader, "ROOT", root)
    monkeypatch.setattr(bootloader.frontier_mod, "ROOT", root)
    monkeypatch.setattr(bootloader.critic_mod, "ROOT", root)
    monkeypatch.setattr(bootloader.tms_mod, "ROOT", root)
    monkeypatch.setattr(bootloader.ethics_mod, "ROOT", root)

    # Redirect key module paths to the temporary repo
    monkeypatch.setattr(bootloader.frontier_mod, "STATE_PATH", root / "memory" / "state.json")
    monkeypatch.setattr(bootloader.frontier_mod, "BACKLOG_PATH", root / "_plans" / "next-development.todo.json")
    monkeypatch.setattr(bootloader.frontier_mod, "TASKS_PATH", root / "agents" / "tasks" / "tasks.json")

    monkeypatch.setattr(bootloader.critic_mod, "STATE_PATH", root / "memory" / "state.json")
    monkeypatch.setattr(bootloader.critic_mod, "BACKLOG_PATH", root / "_plans" / "next-development.todo.json")
    monkeypatch.setattr(bootloader.critic_mod, "CLAIMS_DIR", root / "_bus" / "claims")

    monkeypatch.setattr(bootloader.tms_mod, "STATE_PATH", root / "memory" / "state.json")
    monkeypatch.setattr(bootloader.tms_mod, "PLANS_DIR", root / "_plans")

    monkeypatch.setattr(bootloader.ethics_mod, "BACKLOG_PATH", root / "_plans" / "next-development.todo.json")
    monkeypatch.setattr(bootloader.ethics_mod, "TASKS_PATH", root / "agents" / "tasks" / "tasks.json")
    monkeypatch.setattr(bootloader.ethics_mod, "CLAIMS_DIR", root / "_bus" / "claims")

    return root


def _install_scan_stubs(monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = bootloader.frontier_mod.Candidate(
        source="backlog",
        identifier="ND-1",
        title="Test frontier entry",
        layer="L4",
        systemic_scale=5,
        priority="high",
    )
    entry = bootloader.frontier_mod.FrontierEntry(
        candidate=candidate,
        impact=2.0,
        dependency_weight=1.5,
        confidence_gap=1.1,
        cohesion_gain=1.2,
        effort=1.0,
    )

    monkeypatch.setattr(bootloader.frontier_mod, "compute_frontier", lambda limit: [entry])

    anomalies = [
        {
            "type": "missing_receipts",
            "id": "ND-1",
            "title": "Missing receipts",
            "coord": {"layer": "L5", "systemic_scale": 6},
            "suggested_task": {
                "task_id": "REPAIR-ND-1",
                "summary": "Add receipts",
                "layer": "L5",
                "systemic_scale": 6,
            },
        }
    ]
    monkeypatch.setattr(bootloader.critic_mod, "detect_anomalies", lambda: anomalies)

    conflicts = [
        {
            "type": "conflicting_facts",
            "id": "fact-1",
            "statements": ["A", "B"],
            "coord": {"layer": "L4", "systemic_scale": 4},
            "suggested_plan": {
                "plan_id": "TMS-fact-1",
                "summary": "Resolve fact conflict",
                "layer": "L4",
                "systemic_scale": 4,
            },
        }
    ]
    monkeypatch.setattr(bootloader.tms_mod, "detect_conflicts", lambda: conflicts)

    violations = [
        {
            "type": "task",
            "id": "TASK-9",
            "title": "High risk task",
            "coord": {"layer": "L6", "systemic_scale": 9},
            "receipts": [],
        }
    ]
    monkeypatch.setattr(bootloader.ethics_mod, "detect_violations", lambda: violations)


def test_scan_table_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup_scan_environment(tmp_path, monkeypatch)
    _install_scan_stubs(monkeypatch)

    exit_code = bootloader.main(["scan"])
    assert exit_code == 0

    output = capsys.readouterr().out
    assert "== Frontier ==" in output
    assert "entries: 1" in output
    assert "anomalies: 1" in output
    assert "conflicts: 1" in output
    assert "violations: 1" in output


def test_scan_text_mode_receipts_and_emissions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _setup_scan_environment(tmp_path, monkeypatch)
    _install_scan_stubs(monkeypatch)

    exit_code = bootloader.main(["scan", "--out", "receipts", "--emit-bus", "--emit-plan"])
    assert exit_code == 0

    output = capsys.readouterr().out
    assert "Receipts:" in output
    assert "- frontier: receipts/frontier.json" in output
    assert "- critic: receipts/critic.json" in output
    assert "- tms: receipts/tms.json" in output
    assert "- ethics: receipts/ethics.json" in output
    assert "- ratchet: receipts/ratchet.json" in output
    assert "Bus claims:" in output
    assert "- critic: _bus/claims/REPAIR-ND-1.json" in output
    assert "- ethics: _bus/claims/ETHICS-TASK-9.json" in output
    assert "Plans:" in output
    assert "- _plans/TMS-fact-1.plan.json" in output
    assert "\nRatchet:" in output
    assert "ratchet_index=" in output


def test_scan_json_with_receipts_and_emission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _setup_scan_environment(tmp_path, monkeypatch)
    _install_scan_stubs(monkeypatch)

    exit_code = bootloader.main(
        ["scan", "--format", "json", "--out", "receipts", "--emit-bus", "--emit-plan"]
    )
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)

    assert payload["counts"] == {
        "frontier": 1,
        "critic": 1,
        "tms": 1,
        "ethics": 1,
    }

    receipts_dir = root / "receipts"
    assert (receipts_dir / "frontier.json").exists()
    assert (receipts_dir / "critic.json").exists()
    assert (receipts_dir / "tms.json").exists()
    assert (receipts_dir / "ethics.json").exists()
    assert (receipts_dir / "ratchet.json").exists()

    assert payload["receipts"] == {
        "frontier": "receipts/frontier.json",
        "critic": "receipts/critic.json",
        "tms": "receipts/tms.json",
        "ethics": "receipts/ethics.json",
        "ratchet": "receipts/ratchet.json",
    }

    # Emission should create bus claims and plan skeletons
    bus = payload["emitted_bus"]
    assert bus["critic"] == ["_bus/claims/REPAIR-ND-1.json"]
    assert bus["ethics"] == ["_bus/claims/ETHICS-TASK-9.json"]

    plans = payload["emitted_plans"]
    assert plans == ["_plans/TMS-fact-1.plan.json"]

    # Verify artifacts were written on disk
    critic_claim = root / "_bus" / "claims" / "REPAIR-ND-1.json"
    ethics_claim = root / "_bus" / "claims" / "ETHICS-TASK-9.json"
    plan_file = root / "_plans" / "TMS-fact-1.plan.json"
    assert critic_claim.exists()
    assert ethics_claim.exists()
    assert plan_file.exists()
    history_file = root / "_report" / "usage" / "systemic-scan" / "ratchet-history.jsonl"
    assert history_file.exists()

    ratchet_payload = payload.get("ratchet")
    assert isinstance(ratchet_payload, dict)
    for key in ("coherence_gain", "complexity_added", "closure_velocity", "risk_load", "ratchet_index"):
        assert key in ratchet_payload
    assert "scan_counts" in ratchet_payload
    scan_counts = ratchet_payload["scan_counts"]
    assert scan_counts == payload["counts"]


def test_scan_only_frontier(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup_scan_environment(tmp_path, monkeypatch)
    _install_scan_stubs(monkeypatch)

    exit_code = bootloader.main(["scan", "--only", "frontier"])
    assert exit_code == 0

    output = capsys.readouterr().out
    assert "== Frontier ==" in output
    assert "entries: 1" in output
    assert "== Critic ==" not in output
    assert "== TMS ==" not in output
    assert "== Ethics ==" not in output


def test_scan_summary_counts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup_scan_environment(tmp_path, monkeypatch)
    _install_scan_stubs(monkeypatch)

    exit_code = bootloader.main(
        [
            "scan",
            "--summary",
            "--skip",
            "critic",
            "--skip",
            "tms",
            "--skip",
            "ethics",
        ]
    )
    assert exit_code == 0

    output = capsys.readouterr().out
    assert "Counts:" in output
    assert "- frontier: 1" in output
    assert "==" not in output


def test_scan_skip_all_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup_scan_environment(tmp_path, monkeypatch)
    _install_scan_stubs(monkeypatch)

    exit_code = bootloader.main(
        [
            "scan",
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
    assert exit_code == 2
    output = capsys.readouterr().out
    assert "::error:: no components selected" in output
