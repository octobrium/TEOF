from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.agent import batch_report


def write_log(path: Path, **fields) -> None:
    data = {
        "generated_at": "20250921T181427Z",
        "agent": "codex-1",
        "operator_preset": {"summary": "pass"},
        "receipts_hygiene": {
            "metrics": {
                "plans_missing_receipts": 0,
                "slow_plans": [],
            }
        },
    }
    data.update(fields)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_batch_report_loads_and_formats(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log_dir = tmp_path / "_report" / "usage" / "batch-refinement"
    log_dir.mkdir(parents=True)
    first = log_dir / "batch-refinement-20250921T181427Z.json"
    write_log(first)
    second = log_dir / "batch-refinement-20250921T192427Z.json"
    write_log(second, operator_preset={"summary": "warn"})

    monkeypatch.setattr(batch_report, "LOG_DIR", log_dir)
    logs = batch_report.load_logs()
    assert len(logs) == 2
    formatted = batch_report.format_log(logs[-1])
    assert "warn" in formatted


def test_batch_report_cli_json_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    log_dir = tmp_path / "_report" / "usage" / "batch-refinement"
    log_dir.mkdir(parents=True)
    write_log(log_dir / "batch-refinement-20250921T181427Z.json")

    monkeypatch.setattr(batch_report, "LOG_DIR", log_dir)
    monkeypatch.setattr(batch_report, "ROOT", tmp_path)

    exit_code = batch_report.main(["--json"])
    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output[0]["agent"] == "codex-1"
