from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.autonomy import stress_harness


def _write_scenarios(path: Path, scenarios: list[dict]) -> None:
    path.write_text(json.dumps(scenarios, indent=2), encoding="utf-8")


def test_run_harness_writes_receipt(tmp_path: Path) -> None:
    scenarios_path = tmp_path / "scenarios.json"
    _write_scenarios(
        scenarios_path,
        [
            {
                "name": "missing receipt",
                "type": "missing_receipt",
                "config": {"missing_receipt": True, "expected_result": "fail"},
            },
            {
                "name": "healthy heartbeat",
                "type": "stuck_task",
                "config": {"heartbeat_gap_minutes": 10, "max_gap_minutes": 30, "expected_result": "pass"},
            },
        ],
    )

    output, summary = stress_harness.run_harness(
        scenarios_path=scenarios_path,
        output_path=tmp_path / "receipt.json",
        require_pass=False,
    )

    assert output.exists()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["counts"]["total"] == 2
    assert payload["counts"]["failed"] == 0
    assert "digest" in payload
    assert summary["counts"]["total"] == 2


def test_cli_requires_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    scenarios_path = tmp_path / "scenarios.json"
    _write_scenarios(
        scenarios_path,
        [
            {
                "name": "auth drop",
                "type": "auth_dropout",
                "config": {"drops": 2, "threshold": 1, "expected_result": "pass"},
            }
        ],
    )
    report_dir = tmp_path / "report"
    monkeypatch.setattr(stress_harness, "REPORT_DIR", report_dir)

    exit_code = stress_harness.main([
        "--scenarios",
        str(scenarios_path),
        "--require-pass",
    ])

    assert exit_code == 1
    assert report_dir.exists()
    out = capsys.readouterr().out
    assert "autonomy_stress" in out


def test_invalid_scenario_type(tmp_path: Path) -> None:
    scenarios_path = tmp_path / "scenarios.json"
    _write_scenarios(
        scenarios_path,
        [
            {
                "name": "bad",
                "type": "unknown",
            }
        ],
    )

    with pytest.raises(stress_harness.HarnessError):
        stress_harness.run_harness(
            scenarios_path=scenarios_path,
            output_path=tmp_path / "receipt.json",
            require_pass=False,
        )
