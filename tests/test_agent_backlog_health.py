from __future__ import annotations

import importlib
import json
from pathlib import Path

import tools.agent.backlog_health as backlog_health


def _setup(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "repo"
    next_dev_dir = root / "_plans"
    report_dir = root / "_report" / "usage" / "backlog-health"
    next_dev_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "updated": "2025-10-05T18:20:00Z",
        "items": [
            {
                "id": "ND-001",
                "title": "Example pending",
                "status": "pending",
                "priority": "high",
                "layer": "L5",
                "systemic_scale": 4,
            },
            {
                "id": "ND-002",
                "title": "Example done",
                "status": "done",
            },
        ],
    }
    todo_path = next_dev_dir / "next-development.todo.json"
    todo_path.write_text(json.dumps(payload), encoding="utf-8")

    importlib.reload(backlog_health)
    monkeypatch.setattr(backlog_health, "ROOT", root)
    monkeypatch.setattr(backlog_health, "NEXT_DEV_PATH", todo_path)
    monkeypatch.setattr(backlog_health, "REPORT_DIR", report_dir)

    return todo_path


def test_backlog_health_writes_receipt(tmp_path, monkeypatch, capsys):
    todo_path = _setup(tmp_path, monkeypatch)

    exit_code = backlog_health.main([])
    assert exit_code == 0

    output_payload = json.loads(capsys.readouterr().out)
    receipt_rel = Path(output_payload["receipt"])
    receipt_path = todo_path.parents[1] / receipt_rel
    assert receipt_path.exists()

    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert payload["pending_threshold_breached"]
    assert payload["status_counts"]["pending"] == 1


def test_backlog_health_no_write(tmp_path, monkeypatch, capsys):
    _setup(tmp_path, monkeypatch)

    exit_code = backlog_health.main(["--no-write", "--threshold", "1"])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert not payload["pending_threshold_breached"]
    assert payload["status_counts"]["pending"] == 1
