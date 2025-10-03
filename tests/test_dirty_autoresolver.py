import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from tools.agent import dirty_autoresolver


ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _write_receipt(base: Path, agent: str, captured_at: datetime) -> Path:
    path = base / "_report" / "session" / agent / "dirty-handoff"
    path.mkdir(parents=True, exist_ok=True)
    receipt = path / f"dirty-{captured_at.strftime('%Y%m%dT%H%M%S')}.txt"
    receipt.write_text(
        "\n".join(
            [
                "# dirty handoff",
                f"# agent={agent}",
                f"# captured_at={captured_at.strftime(ISO_FMT)}",
                "",
                " M docs/file.py",
            ]
        ),
        encoding="utf-8",
    )
    return receipt


def test_collect_receipts(tmp_path, monkeypatch):
    monkeypatch.setattr(dirty_autoresolver, "ROOT", tmp_path)
    now = datetime(2025, 10, 3, 5, 0, tzinfo=timezone.utc)
    recent = now - timedelta(minutes=10)
    stale = now - timedelta(minutes=70)
    _write_receipt(tmp_path, "codex-2", recent)
    _write_receipt(tmp_path, "codex-3", stale)

    statuses = dirty_autoresolver.collect_receipts(now)
    assert {entry.agent_id for entry in statuses} == {"codex-2", "codex-3"}


def test_classification_and_exit_codes(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(dirty_autoresolver, "ROOT", tmp_path)
    now = datetime(2025, 10, 3, 5, 0, tzinfo=timezone.utc)
    recent = now - timedelta(minutes=5)
    warn = now - timedelta(minutes=45)
    fail = now - timedelta(minutes=90)
    _write_receipt(tmp_path, "codex-2", recent)
    _write_receipt(tmp_path, "codex-3", warn)
    _write_receipt(tmp_path, "codex-4", fail)

    exit_code = dirty_autoresolver.main([
        "--warn-age-minutes",
        "30",
        "--max-age-minutes",
        "60",
        "--now",
        now.strftime(ISO_FMT),
        "--output",
        str(tmp_path / "summary.json"),
    ])

    captured = capsys.readouterr().out
    assert "codex-3" in captured
    assert "codex-4" in captured
    assert exit_code == 2
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    statuses = {entry["agent_id"]: entry["status"] for entry in summary["agents"]}
    assert statuses["codex-2"] == dirty_autoresolver.STATUS_OK
    assert statuses["codex-3"] == dirty_autoresolver.STATUS_WARN
    assert statuses["codex-4"] == dirty_autoresolver.STATUS_FAIL


def test_bus_message(monkeypatch, tmp_path):
    messages = []

    def fake_log_message(**kwargs):
        messages.append(kwargs)

    monkeypatch.setattr(dirty_autoresolver.bus_message, "log_message", fake_log_message)
    monkeypatch.setattr(dirty_autoresolver, "ROOT", tmp_path)
    now = datetime(2025, 10, 3, 5, 0, tzinfo=timezone.utc)
    _write_receipt(tmp_path, "codex-2", now - timedelta(minutes=100))

    output_path = tmp_path / "out.json"
    exit_code = dirty_autoresolver.main([
        "--bus-message",
        "--output",
        str(output_path),
        "--now",
        now.strftime(ISO_FMT),
        "--task",
        "manager-report",
    ])

    assert exit_code == 2
    assert len(messages) == 1
    message = messages[0]
    assert message["task_id"] == "manager-report"
    assert output_path.exists()
    assert output_path.relative_to(tmp_path).name in message["receipts"][0]
