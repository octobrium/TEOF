from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.agent import session_brief


def _write_jsonl(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + "\n")


def test_session_brief_outputs_claim_and_logs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(session_brief, "CLAIMS_DIR", tmp_path / "claims")
    monkeypatch.setattr(session_brief, "EVENT_LOG", tmp_path / "events.jsonl")
    monkeypatch.setattr(session_brief, "MESSAGES_DIR", tmp_path / "messages")

    claim_path = session_brief.CLAIMS_DIR / "QUEUE-150.json"
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    claim_path.write_text(
        json.dumps(
            {
                "agent_id": "codex-4",
                "task_id": "QUEUE-150",
                "status": "paused",
                "plan_id": "2025-plan",
                "branch": "agent/codex-4/queue-150",
                "claimed_at": "2025-09-18T20:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    _write_jsonl(
        session_brief.EVENT_LOG,
        [
            {
                "ts": "2025-09-18T20:05:00Z",
                "agent_id": "codex-4",
                "event": "status",
                "task_id": "QUEUE-150",
                "summary": "Working on helper",
            },
            {
                "ts": "2025-09-18T20:10:00Z",
                "agent_id": "codex-4",
                "event": "complete",
                "task_id": "QUEUE-150",
                "summary": "Helper done",
            },
        ],
    )

    task_messages = session_brief.MESSAGES_DIR / "QUEUE-150.jsonl"
    _write_jsonl(
        task_messages,
        [
            {
                "ts": "2025-09-18T20:06:00Z",
                "from": "codex-1",
                "type": "status",
                "task_id": "QUEUE-150",
                "summary": "Manager review scheduled",
            }
        ],
    )

    exit_code = session_brief.main(["--task", "QUEUE-150", "--limit", "2"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Task: QUEUE-150" in out
    assert "Agent: codex-4" in out
    assert "Events" in out and "complete" in out
    assert "Messages" in out and "Manager review scheduled" in out


def test_session_brief_without_claim(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(session_brief, "CLAIMS_DIR", tmp_path / "claims")
    monkeypatch.setattr(session_brief, "EVENT_LOG", tmp_path / "events.jsonl")
    monkeypatch.setattr(session_brief, "MESSAGES_DIR", tmp_path / "messages")

    exit_code = session_brief.main(["--task", "QUEUE-151"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "No claim found" in out


def test_session_brief_operator_preset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    repo_root = tmp_path
    claims_dir = repo_root / "_bus" / "claims"
    events_log = repo_root / "events.jsonl"
    messages_dir = repo_root / "_bus" / "messages"
    session_dir = repo_root / "_report" / "session"
    planner_dir = repo_root / "_report" / "planner" / "validate"
    agent_reports = repo_root / "_report" / "agent"
    usage_dir = repo_root / "_report" / "usage"
    quickstart_dir = repo_root / "artifacts" / "ocers_out" / "latest"

    monkeypatch.setattr(session_brief, "ROOT", repo_root)
    monkeypatch.setattr(session_brief, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(session_brief, "EVENT_LOG", events_log)
    monkeypatch.setattr(session_brief, "MESSAGES_DIR", messages_dir)
    monkeypatch.setattr(session_brief, "SESSION_DIR", session_dir)
    monkeypatch.setattr(session_brief, "PLANNER_VALIDATE_DIR", planner_dir)
    monkeypatch.setattr(session_brief, "SESSION_BRIEF_DIR", agent_reports)
    monkeypatch.setattr(session_brief, "USAGE_REPORT_DIR", usage_dir)
    monkeypatch.setattr(session_brief, "QUICKSTART_LATEST", quickstart_dir)
    monkeypatch.setattr(session_brief, "MANIFEST_PATH", repo_root / "AGENT_MANIFEST.json")

    # Seed claim, events, and manager message for consistency
    claim_path = claims_dir / "QUEUE-160.json"
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    claim_path.write_text(
        json.dumps(
            {
                "agent_id": "codex-1",
                "task_id": "QUEUE-160",
                "status": "active",
                "plan_id": "2025-plan",
            }
        ),
        encoding="utf-8",
    )

    _write_jsonl(events_log, [])
    _write_jsonl(messages_dir / "QUEUE-160.jsonl", [])

    manifest_path = repo_root / "AGENT_MANIFEST.json"
    manifest_path.write_text(json.dumps({"agent_id": "codex-1"}), encoding="utf-8")

    tail_path = session_dir / "codex-1" / "manager-report-tail.txt"
    tail_path.parent.mkdir(parents=True, exist_ok=True)
    tail_path.write_text("recent manager tail", encoding="utf-8")

    planner_path = planner_dir / "summary-20250921T000000Z.json"
    planner_path.parent.mkdir(parents=True, exist_ok=True)
    planner_path.write_text("{}\n", encoding="utf-8")

    quickstart_file = quickstart_dir / "brief.json"
    quickstart_file.parent.mkdir(parents=True, exist_ok=True)
    quickstart_file.write_text("{}\n", encoding="utf-8")

    task_sync_dir = agent_reports / "codex-1" / "task_sync"
    task_sync_dir.mkdir(parents=True, exist_ok=True)
    (task_sync_dir / "summary.json").write_text("{}\n", encoding="utf-8")

    usage_dir.mkdir(parents=True, exist_ok=True)
    (usage_dir / "receipts-index-sample.jsonl").write_text("{}\n", encoding="utf-8")
    (usage_dir / "receipts-hygiene-summary.json").write_text(
        json.dumps(
            {
                "metrics": {
                    "plans_missing_receipts": 0,
                    "slow_plans": [],
                }
            }
        ),
        encoding="utf-8",
    )

    output_path = repo_root / "session-brief.json"
    exit_code = session_brief.main(
        [
            "--task",
            "QUEUE-160",
            "--limit",
            "1",
            "--preset",
            "operator",
            "--agent",
            "codex-1",
            "--output",
            str(output_path),
        ]
    )
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Operator preset summary" in output

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["preset"] == "operator"
    statuses = {item["id"]: item["status"] for item in data["checklist"]}
    assert statuses["manager_tail"] == "pass"
    assert statuses["planner_validate"] == "pass"
    assert statuses["quickstart_receipts"] == "pass"
    assert statuses["receipts_index"] == "pass"
    assert statuses["receipts_hygiene"] == "pass"
    assert data["summary"] in {"pass", "warn"}


def test_session_brief_operator_preset_flags_failures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path
    claims_dir = repo_root / "_bus" / "claims"
    events_log = repo_root / "events.jsonl"
    messages_dir = repo_root / "_bus" / "messages"
    session_dir = repo_root / "_report" / "session"
    planner_dir = repo_root / "_report" / "planner" / "validate"
    agent_reports = repo_root / "_report" / "agent"
    usage_dir = repo_root / "_report" / "usage"
    quickstart_dir = repo_root / "artifacts" / "ocers_out" / "latest"

    monkeypatch.setattr(session_brief, "ROOT", repo_root)
    monkeypatch.setattr(session_brief, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(session_brief, "EVENT_LOG", events_log)
    monkeypatch.setattr(session_brief, "MESSAGES_DIR", messages_dir)
    monkeypatch.setattr(session_brief, "SESSION_DIR", session_dir)
    monkeypatch.setattr(session_brief, "PLANNER_VALIDATE_DIR", planner_dir)
    monkeypatch.setattr(session_brief, "SESSION_BRIEF_DIR", agent_reports)
    monkeypatch.setattr(session_brief, "USAGE_REPORT_DIR", usage_dir)
    monkeypatch.setattr(session_brief, "QUICKSTART_LATEST", quickstart_dir)
    monkeypatch.setattr(session_brief, "MANIFEST_PATH", repo_root / "AGENT_MANIFEST.json")

    claim_path = claims_dir / "QUEUE-170.json"
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    claim_path.write_text(
        json.dumps(
            {
                "agent_id": "codex-2",
                "task_id": "QUEUE-170",
                "status": "done",
            }
        ),
        encoding="utf-8",
    )

    _write_jsonl(events_log, [])
    _write_jsonl(messages_dir / "QUEUE-170.jsonl", [])

    output_path = repo_root / "sb.json"
    exit_code = session_brief.main(
        [
            "--task",
            "QUEUE-170",
            "--preset",
            "operator",
            "--output",
            str(output_path),
        ]
    )
    assert exit_code == 0
    data = json.loads(output_path.read_text(encoding="utf-8"))
    statuses = {item["id"]: item["status"] for item in data["checklist"]}
    assert statuses["manager_tail"] == "fail"
    assert statuses["receipts_hygiene"] == "warn"
    assert data["summary"] == "fail"
