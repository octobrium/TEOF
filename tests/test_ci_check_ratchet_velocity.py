import json
import os
import sys
from pathlib import Path

import pytest

from scripts.ci import check_ratchet_velocity


@pytest.fixture()
def history_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "ratchet-history.jsonl"
    monkeypatch.setattr(check_ratchet_velocity, "HISTORY_PATH", path)
    return path


def write_history(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_guard_passes_when_history_missing(history_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = check_ratchet_velocity.main()
    assert exit_code == 0
    err = capsys.readouterr().err
    assert "ratchet history missing" in err


def test_guard_passes_with_healthy_metrics(history_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_history(
        history_path,
        {
            "ratchet_index": 1.05,
            "closure_velocity": 0.5,
            "risk_load": 2.0,
            "complexity_added": 3.0,
        },
    )
    monkeypatch.setenv("TEOF_RATCHET_MAX_RISK_MULTIPLIER", "2.0")
    exit_code = check_ratchet_velocity.main()
    assert exit_code == 0


def test_guard_fails_when_index_below_threshold(history_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_history(
        history_path,
        {
            "ratchet_index": 0.7,
            "closure_velocity": 0.4,
            "risk_load": 1.0,
            "complexity_added": 2.0,
        },
    )
    monkeypatch.setenv("TEOF_RATCHET_MIN_INDEX", "0.9")
    exit_code = check_ratchet_velocity.main()
    assert exit_code == 1
