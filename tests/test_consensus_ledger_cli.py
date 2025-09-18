from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.consensus import ledger as ledger_cli


@pytest.fixture()
def sample_ledger(tmp_path: Path) -> Path:
    content = """batch_ts,total_items,avg_score,total_score,avg_risk,accept_rate,notes\n""" \
        "20250917T170236Z,5,1.200,6,0.250,0.800,first\n" \
        "20250918T010000Z,3,1.500,5,,0.667,second\n"
    path = tmp_path / "ledger.csv"
    path.write_text(content, encoding="utf-8")
    return path


def test_table_output(sample_ledger: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = ledger_cli.main(["--ledger", str(sample_ledger)])
    assert exit_code == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert out[0].startswith("batch_ts")
    assert "20250917T170236Z" in out[2]


def test_jsonl_filtering(sample_ledger: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = ledger_cli.main(
        [
            "--ledger",
            str(sample_ledger),
            "--format",
            "jsonl",
            "--decision",
            "20250918T010000Z",
        ]
    )
    assert exit_code == 0
    out_lines = capsys.readouterr().out.strip().splitlines()
    assert len(out_lines) == 1
    payload = json.loads(out_lines[0])
    assert payload["batch_ts"] == "20250918T010000Z"


def test_since_filter(sample_ledger: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = ledger_cli.main(
        [
            "--ledger",
            str(sample_ledger),
            "--format",
            "jsonl",
            "--since",
            "2025-09-18T00:00:00Z",
        ]
    )
    assert exit_code == 0
    out_lines = capsys.readouterr().out.strip().splitlines()
    assert len(out_lines) == 1
    payload = json.loads(out_lines[0])
    assert payload["batch_ts"] == "20250918T010000Z"


def test_output_receipt(sample_ledger: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    receipt = tmp_path / "receipt.jsonl"
    exit_code = ledger_cli.main(
        [
            "--ledger",
            str(sample_ledger),
            "--format",
            "jsonl",
            "--output",
            str(receipt),
        ]
    )
    assert exit_code == 0
    assert receipt.exists()
    saved = receipt.read_text(encoding="utf-8").strip().splitlines()
    assert len(saved) == 2
    assert json.loads(saved[0])["batch_ts"] == "20250917T170236Z"


def test_missing_ledger(tmp_path: Path) -> None:
    missing = tmp_path / "missing.csv"
    with pytest.raises(SystemExit) as excinfo:
        ledger_cli.main(["--ledger", str(missing)])
    assert excinfo.value.code == 2
