from __future__ import annotations

import json
from pathlib import Path

from tools.autonomy.bus_guard import BusGuard


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_bus_guard_autofix_claim(tmp_path):
    claims_dir = tmp_path / "_bus" / "claims"
    _write_json(
        claims_dir / "QUEUE-057.json",
        {
            "task_id": "QUEUE-057",
            "status": "pending",
            "agent_id": "codex-tier2",
            "branch": "main",
            "plan_id": "demo-plan",
        },
    )
    guard = BusGuard(tmp_path, now_fn=lambda: "2025-01-02T03:04:05Z")

    issues = guard.run(autofix=True)

    claim = json.loads((claims_dir / "QUEUE-057.json").read_text())
    assert claim["status"] == "active"
    assert claim["branch"].startswith("agent/codex-tier2/queue-057")
    assert claim["claimed_at"] == "2025-01-02T03:04:05Z"
    assert any(issue.fixed for issue in issues)
    assert all(issue.fixed for issue in issues)


def test_bus_guard_reports_when_not_fixed(tmp_path):
    assignments_dir = tmp_path / "_bus" / "assignments"
    _write_json(
        assignments_dir / "QUEUE-031.json",
        {
            "task_id": "QUEUE-031",
            "manager": "codex-1",
            "status": "unassigned",
            "notes": "Awaiting claim",
        },
    )
    guard = BusGuard(tmp_path)

    issues = guard.run(autofix=False)

    assert any(issue.scope == "assignments" for issue in issues)


def test_bus_guard_autofix_manager_messages(tmp_path):
    messages_dir = tmp_path / "_bus" / "messages"
    messages_dir.mkdir(parents=True, exist_ok=True)
    (messages_dir / "manager-report.jsonl").write_text(
        '{"agent_id":"codex-1","event":"status","summary":"demo","ts":"2025-01-02T03:04:05"}\n',
        encoding="utf-8",
    )
    guard = BusGuard(tmp_path, now_fn=lambda: "2025-01-02T03:04:05Z")

    issues = guard.run(autofix=True)

    contents = (messages_dir / "manager-report.jsonl").read_text().strip()
    data = json.loads(contents)
    assert data["task_id"] == "manager-report"
    assert data["ts"].endswith("Z")
    assert any(issue.fixed for issue in issues)
