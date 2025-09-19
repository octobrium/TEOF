import json
from pathlib import Path

import pytest

from tools.agent import manager_report
from tools.agent import bus_event


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path
    (root / "_bus" / "events").mkdir(parents=True)
    (root / "_bus" / "messages").mkdir(parents=True)
    (root / "_bus" / "assignments").mkdir(parents=True)
    (root / "_bus" / "claims").mkdir(parents=True)
    (root / "agents").mkdir()
    (root / "_report" / "manager").mkdir(parents=True)

    tasks_path = root / "agents" / "tasks" / "tasks.json"
    tasks_path.parent.mkdir(parents=True, exist_ok=True)
    tasks_path.write_text(json.dumps({"tasks": []}), encoding="utf-8")

    monkeypatch.setattr(manager_report, "ROOT", root)
    monkeypatch.setattr(manager_report, "ASSIGN_DIR", root / "_bus" / "assignments")
    monkeypatch.setattr(manager_report, "CLAIMS_DIR", root / "_bus" / "claims")
    monkeypatch.setattr(manager_report, "MESSAGES_DIR", root / "_bus" / "messages")
    monkeypatch.setattr(manager_report, "REPORT_DIR", root / "_report" / "manager")
    monkeypatch.setattr(manager_report, "TASKS_FILE", tasks_path)

    monkeypatch.setattr(bus_event, "ROOT", root)
    monkeypatch.setattr(bus_event, "EVENT_LOG", root / "_bus" / "events" / "events.jsonl")
    monkeypatch.setattr(bus_event, "MANIFEST_PATH", root / "AGENT_MANIFEST.json")
    (root / "AGENT_MANIFEST.json").write_text(json.dumps({"agent_id": "codex-manager"}), encoding="utf-8")

    return root


def test_manager_report_writes_file(repo: Path):
    report_dir = repo / "_report" / "manager"
    rc = manager_report.main(["--manager", "codex-manager"])
    assert rc == 0
    reports = list(report_dir.glob("manager-report-*.md"))
    assert reports, "manager report file should be created"


def test_manager_report_logs_heartbeat(repo: Path):
    events_path = repo / "_bus" / "events" / "events.jsonl"
    rc = manager_report.main([
        "--manager",
        "codex-manager",
        "--log-heartbeat",
        "--heartbeat-summary",
        "codex-manager heartbeat",
        "--heartbeat-shift",
        "mid",
    ])
    assert rc == 0
    entries = [
        json.loads(line)
        for line in events_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    heartbeat = next(
        entry
        for entry in entries
        if entry.get("agent_id") == "codex-manager" and entry.get("summary") == "codex-manager heartbeat"
    )
    assert heartbeat.get("shift") == "mid"
