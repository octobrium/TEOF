from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tools.consensus import dashboard


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def _setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[str, str]:
    events_path = tmp_path / "_bus" / "events" / "events.jsonl"
    manager_path = tmp_path / "_bus" / "messages" / "manager-report.jsonl"
    assignments_dir = tmp_path / "_bus" / "assignments"
    assignments_dir.mkdir(parents=True)

    base = datetime(2025, 9, 18, 19, 40, tzinfo=timezone.utc)
    def iso(minutes: int) -> str:
        return (base + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")

    events = [
        {"ts": iso(0), "agent_id": "codex-1", "event": "status", "task_id": "QUEUE-030", "summary": "ledger plan queued"},
        {"ts": iso(5), "agent_id": "codex-4", "event": "complete", "task_id": "QUEUE-030", "summary": "ledger CLI shipped", "receipts": ["_report/agent/codex-4/ledger/pytest.json"]},
        {"ts": iso(3), "agent_id": "codex-4", "event": "status", "task_id": "QUEUE-033", "summary": "dashboard prototype"},
    ]
    _write_jsonl(events_path, events)

    manager_msgs = [
        {"ts": iso(1), "from": "codex-1", "type": "status", "task_id": "QUEUE-030", "summary": "consensus ledger prepping"},
        {"ts": iso(4), "from": "codex-1", "type": "status", "task_id": "QUEUE-033", "summary": "dashboard needs owner"},
    ]
    _write_jsonl(manager_path, manager_msgs)

    assignment_payload = {"task_id": "QUEUE-030", "manager": "codex-1"}
    (assignments_dir / "QUEUE-030.json").write_text(json.dumps(assignment_payload), encoding="utf-8")

    monkeypatch.setattr(dashboard, "ROOT", tmp_path)
    monkeypatch.setattr(dashboard, "EVENT_LOG", events_path)
    monkeypatch.setattr(dashboard, "MANAGER_REPORT", manager_path)
    monkeypatch.setattr(dashboard, "ASSIGNMENTS_DIR", assignments_dir)
    return iso(0), iso(5)


def test_dashboard_table_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup(tmp_path, monkeypatch)
    exit_code = dashboard.main(["--task", "QUEUE-030", "--task", "QUEUE-033", "--format", "table"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "QUEUE-030" in out
    assert "codex-1" in out
    assert "ledger CLI shipped" not in out  # summary excluded, only metadata
    assert "_report/agent/codex-4/ledger/pytest.json" in out
    assert "QUEUE-033" in out


def test_dashboard_json_since_filter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    start, end = _setup(tmp_path, monkeypatch)
    exit_code = dashboard.main([
        "--task",
        "QUEUE-030",
        "--task",
        "QUEUE-033",
        "--format",
        "json",
        "--since",
        end,
    ])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    # Since filter excludes older events, leaving latest entries only.
    assert len(payload) == 2
    ledger = next(item for item in payload if item["task_id"] == "QUEUE-030")
    assert ledger["status"] == "complete"
    assert ledger["receipts"] == ["_report/agent/codex-4/ledger/pytest.json"]
    dashboard_item = next(item for item in payload if item["task_id"] == "QUEUE-033")
    assert dashboard_item["status"] == "unknown"
    assert dashboard_item["event_count"] == 0


def test_dashboard_markdown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _setup(tmp_path, monkeypatch)
    exit_code = dashboard.main(["--task", "QUEUE-030", "--format", "markdown"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "| Task |" in out
    assert "| QUEUE-030 |" in out
