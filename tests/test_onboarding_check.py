from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from tools.agent import onboarding_check


def _seed_repo(root: Path) -> None:
    (root / "agents" / "tasks").mkdir(parents=True, exist_ok=True)
    (root / "agents" / "tasks" / "tasks.json").write_text(
        json.dumps(
            {
                "version": 1,
                "tasks": [
                    {
                        "id": "QUEUE-100",
                        "title": "Open task",
                        "status": "open",
                        "priority": "high",
                        "assigned_by": "codex-1",
                        "receipts": [],
                    },
                    {
                        "id": "QUEUE-101",
                        "title": "Closed task",
                        "status": "done",
                        "priority": "medium",
                        "receipts": [],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    manifest = {"agent_id": "codex-test"}
    (root / "AGENT_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_onboarding_check_writes_receipts(tmp_path: Path, monkeypatch) -> None:
    _seed_repo(tmp_path)

    monkeypatch.setattr(onboarding_check, "ROOT", tmp_path)
    monkeypatch.setattr(onboarding_check, "MANIFEST_PATH", tmp_path / "AGENT_MANIFEST.json")
    monkeypatch.setattr(onboarding_check, "_iso_now", lambda: "2025-09-24T00:00:00Z")

    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)

    rc = onboarding_check.main([])
    assert rc == 0

    out_dir = tmp_path / "_report" / "onboarding" / "codex-test"
    status_path = out_dir / "status-2025-09-24T00:00:00Z.md"
    tasks_json_path = out_dir / "tasks-2025-09-24T00:00:00Z.json"
    tasks_table_path = out_dir / "tasks-2025-09-24T00:00:00Z.txt"
    summary_path = out_dir / "onboarding-2025-09-24T00:00:00Z.json"

    assert status_path.exists()
    assert tasks_json_path.exists()
    assert tasks_table_path.exists()
    assert summary_path.exists()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["agent"] == "codex-test"
    assert summary["status_receipt"].endswith("status-2025-09-24T00:00:00Z.md")
    assert summary["warnings"] == [
        "QUEUE-100: open with no assignment or active claim",
    ]

    stdout = buffer.getvalue()
    assert "Onboarding check receipts" in stdout
    assert "warnings" in stdout.lower()
