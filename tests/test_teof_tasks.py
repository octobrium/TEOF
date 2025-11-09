from __future__ import annotations

import io
import json
import sys
from dataclasses import replace
from pathlib import Path

import teof.bootloader as bootloader
from teof import tasks_report
from teof.tasks_report import TaskRecord
from tools.autonomy import receipt_utils


def _setup_repo(
    root: Path,
    *,
    extra_tasks: list[dict] | None = None,
    extra_assignments: dict[str, dict] | None = None,
    extra_claims: dict[str, dict] | None = None,
) -> None:
    tasks_dir = root / "agents" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    base_tasks = [
        {
            "id": "QUEUE-100",
            "title": "Implement tasks CLI",
            "status": "open",
            "priority": "high",
            "role": "engineer",
            "plan_id": "2025-09-24-teof-tasks",
            "notes": "Ensure tasks CLI mirrors assignments",
            "assigned_by": "codex-1",
            "branch": "agent/codex-9/queue-100",
            "receipts": ["_report/agent/demo/tasks-cli.json"],
        },
        {
            "id": "QUEUE-101",
            "title": "Completed task",
            "status": "done",
            "priority": "low",
            "role": "engineer",
        },
    ]
    if extra_tasks:
        base_tasks.extend(extra_tasks)
    (tasks_dir / "tasks.json").write_text(
        json.dumps({"version": 1, "tasks": base_tasks}),
        encoding="utf-8",
    )

    assignments_dir = root / "_bus" / "assignments"
    assignments_dir.mkdir(parents=True, exist_ok=True)
    assignment_payloads = {
        "QUEUE-100": {
            "task_id": "QUEUE-100",
            "engineer": "codex-9",
            "manager": "codex-1",
            "plan_id": "2025-09-24-teof-tasks",
            "branch": "agent/codex-9/queue-100",
            "note": "Priority for new contributor onboarding",
            "assigned_at": "2025-09-24T00:00:00Z",
        }
    }
    if extra_assignments:
        assignment_payloads.update(extra_assignments)
    for task_id, payload in assignment_payloads.items():
        (assignments_dir / f"{task_id}.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    claims_dir = root / "_bus" / "claims"
    claims_dir.mkdir(parents=True, exist_ok=True)
    claim_payloads = {
        "QUEUE-100": {
            "task_id": "QUEUE-100",
            "agent_id": "codex-9",
            "status": "active",
            "branch": "agent/codex-9/queue-100",
            "plan_id": "2025-09-24-teof-tasks",
            "claimed_at": "2025-09-24T01:00:00Z",
        }
    }
    if extra_claims:
        claim_payloads.update(extra_claims)
    for task_id, payload in claim_payloads.items():
        (claims_dir / f"{task_id}.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )


def _run_tasks_cli(monkeypatch, args: list[str]) -> dict:
    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)
    result = bootloader.main(["tasks", "--format", "json", *args])
    assert result == 0
    return json.loads(buffer.getvalue())


def _patch_receipts(monkeypatch, root: Path) -> None:
    plans_dir = root / "_plans"
    guards_root = root / "_report" / "ethics" / "guards"
    plans_dir.mkdir(parents=True, exist_ok=True)
    guards_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(receipt_utils, "ROOT", root)
    monkeypatch.setattr(receipt_utils, "DEFAULT_PLANS_DIR", plans_dir)
    monkeypatch.setattr(receipt_utils, "GUARDS_DIR", guards_root)


def test_cli_tasks_json(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(tasks_report, "ROOT", tmp_path)
    _patch_receipts(monkeypatch, tmp_path)

    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)

    result = bootloader.main(["tasks", "--format", "json"])
    assert result == 0

    payload = json.loads(buffer.getvalue())
    tasks = payload["tasks"]
    assert len(tasks) == 1  # default excludes completed tasks
    record = tasks[0]
    assert record["task_id"] == "QUEUE-100"
    assert record["assignment_engineer"] == "codex-9"
    assert record["claim_agent"] == "codex-9"
    assert record["plan_id"] == "2025-09-24-teof-tasks"
    assert payload["warnings"] == []


def test_cli_tasks_table_includes_done_when_requested(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(tasks_report, "ROOT", tmp_path)
    _patch_receipts(monkeypatch, tmp_path)

    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)

    result = bootloader.main(["tasks", "--all"])
    assert result == 0
    output = buffer.getvalue()
    assert "QUEUE-100" in output
    assert "QUEUE-101" in output
    assert "Warnings:" in output
    assert "QUEUE-101: marked done but no receipts recorded" in output


def test_cli_tasks_status_filter_includes_done(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(tasks_report, "ROOT", tmp_path)
    _patch_receipts(monkeypatch, tmp_path)

    payload = _run_tasks_cli(monkeypatch, ["--all", "--status", "DONE"])
    tasks = payload["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["task_id"] == "QUEUE-101"
    assert tasks[0]["status"] == "done"


def test_cli_tasks_priority_and_agent_filters(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(
        tmp_path,
        extra_tasks=[
            {
                "id": "QUEUE-200",
                "title": "Medium priority task",
                "status": "open",
                "priority": "medium",
                "role": "engineer",
            },
            {
                "id": "QUEUE-201",
                "title": "Claim-only context",
                "status": "open",
                "priority": "low",
                "role": "engineer",
            },
        ],
        extra_assignments={
            "QUEUE-200": {
                "task_id": "QUEUE-200",
                "engineer": "codex-10",
                "manager": "codex-2",
                "plan_id": "2025-10-01-medium-task",
                "assigned_at": "2025-10-01T00:00:00Z",
            }
        },
        extra_claims={
            "QUEUE-201": {
                "task_id": "QUEUE-201",
                "agent_id": "codex-11",
                "status": "active",
                "claimed_at": "2025-10-02T00:00:00Z",
            }
        },
    )
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(tasks_report, "ROOT", tmp_path)
    _patch_receipts(monkeypatch, tmp_path)
    _patch_receipts(monkeypatch, tmp_path)

    payload = _run_tasks_cli(monkeypatch, ["--priority", "medium", "--agent", "codex-10"])
    tasks = payload["tasks"]
    assert [task["task_id"] for task in tasks] == ["QUEUE-200"]
    assert tasks[0]["assignment_engineer"] == "codex-10"

    payload = _run_tasks_cli(monkeypatch, ["--agent", "CODEX-11"])
    tasks = payload["tasks"]
    assert [task["task_id"] for task in tasks] == ["QUEUE-201"]
    assert tasks[0]["claim_agent"] == "codex-11"


def test_cli_tasks_handles_broken_pipe_in_json(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(tasks_report, "ROOT", tmp_path)
    _patch_receipts(monkeypatch, tmp_path)

    class _BrokenStdout:
        def write(self, _: str) -> int:
            raise BrokenPipeError()

        def flush(self) -> None:
            pass

    monkeypatch.setattr(sys, "stdout", _BrokenStdout())
    result = bootloader.main(["tasks", "--format", "json"])
    assert result == 0


def test_cli_tasks_filters_by_agent(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(tasks_report, "ROOT", tmp_path)
    _patch_receipts(monkeypatch, tmp_path)

    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)

    result = bootloader.main(["tasks", "--format", "json", "--agent", "codex-9"])
    assert result == 0
    payload = json.loads(buffer.getvalue())
    assert [task["task_id"] for task in payload["tasks"]] == ["QUEUE-100"]

    buffer.truncate(0)
    buffer.seek(0)
    result = bootloader.main(["tasks", "--format", "json", "--agent", "codex-1"])
    assert result == 0
    payload = json.loads(buffer.getvalue())
    assert payload["tasks"] == []


def test_cli_tasks_summary_table(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(tasks_report, "ROOT", tmp_path)
    _patch_receipts(monkeypatch, tmp_path)

    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)

    result = bootloader.main(["tasks", "--summary"])
    assert result == 0
    output = buffer.getvalue()
    assert "Summary:" in output
    assert "- total: 1" in output
    assert "by status" in output
    assert "open without owner" in output
    assert "Warnings:" in output


def test_cli_tasks_summary_json(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(tasks_report, "ROOT", tmp_path)
    _patch_receipts(monkeypatch, tmp_path)

    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)

    result = bootloader.main(["tasks", "--format", "json", "--summary"])
    assert result == 0
    payload = json.loads(buffer.getvalue())
    assert payload["summary_only"] is True
    assert payload["tasks"] == []
    summary = payload["summary"]
    assert summary["total"] == 1
    assert summary["status"]["open"] == 1
    assert summary["priority"]["high"] == 1
    assert summary["assignments"] == 1
    assert summary["claims"] == 1


def test_cli_tasks_limit_restricts_output(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(
        tmp_path,
        extra_tasks=[
            {
                "id": "QUEUE-102",
                "title": "Second open task",
                "status": "open",
                "priority": "medium",
                "role": "engineer",
            }
        ],
    )
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(tasks_report, "ROOT", tmp_path)
    _patch_receipts(monkeypatch, tmp_path)

    payload = _run_tasks_cli(monkeypatch, ["--limit", "1"])
    assert payload["limit_applied"] == 1
    assert payload["total_filtered"] == 2
    assert len(payload["tasks"]) == 1
    assert payload["tasks"][0]["task_id"] == "QUEUE-100"
    assert any("QUEUE-102" in warning for warning in payload["warnings"])


def test_cli_tasks_table_limit_note(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(
        tmp_path,
        extra_tasks=[
            {
                "id": "QUEUE-103",
                "title": "Open task (table limit)",
                "status": "open",
                "priority": "low",
                "role": "engineer",
            }
        ],
    )
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(tasks_report, "ROOT", tmp_path)
    _patch_receipts(monkeypatch, tmp_path)

    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)

    result = bootloader.main(["tasks", "--limit", "1"])
    assert result == 0
    output = buffer.getvalue()
    assert "Showing 1 of 2 tasks (limit=1)." in output


def test_cli_tasks_plan_filter(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(
        tmp_path,
        extra_tasks=[
            {
                "id": "QUEUE-300",
                "title": "Claim-only plan linkage",
                "status": "open",
                "priority": "medium",
                "role": "engineer",
            }
        ],
        extra_claims={
            "QUEUE-300": {
                "task_id": "QUEUE-300",
                "agent_id": "codex-12",
                "status": "active",
                "plan_id": "2025-10-02-claimed-only",
                "claimed_at": "2025-10-02T00:00:00Z",
            }
        },
    )
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(tasks_report, "ROOT", tmp_path)
    _patch_receipts(monkeypatch, tmp_path)

    payload = _run_tasks_cli(monkeypatch, ["--plan", "2025-09-24-teof-tasks"])
    assert [task["task_id"] for task in payload["tasks"]] == ["QUEUE-100"]

    payload = _run_tasks_cli(monkeypatch, ["--plan", "2025-10-02-claimed-only"])
    assert [task["task_id"] for task in payload["tasks"]] == ["QUEUE-300"]


def test_tasks_cli_includes_guard_receipts(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    guard_dir = tmp_path / "_report" / "ethics" / "guards" / "2025-11-09"
    guard_dir.mkdir(parents=True, exist_ok=True)
    guard_path = guard_dir / "queue-100-ethics.json"
    guard_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(tasks_report, "ROOT", tmp_path)
    _patch_receipts(monkeypatch, tmp_path)

    payload = _run_tasks_cli(monkeypatch, [])
    receipts = payload["tasks"][0]["receipts"]
    assert guard_path.relative_to(tmp_path).as_posix() in receipts


def test_tasks_cli_uses_claim_status_when_task_missing(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    tasks_path = tmp_path / "agents" / "tasks" / "tasks.json"
    payload = json.loads(tasks_path.read_text(encoding="utf-8"))
    payload["tasks"] = [entry for entry in payload["tasks"] if entry["id"] != "QUEUE-100"]
    tasks_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    monkeypatch.setattr(tasks_report, "ROOT", tmp_path)
    _patch_receipts(monkeypatch, tmp_path)

    payload = _run_tasks_cli(monkeypatch, [])
    assert payload["tasks"][0]["status"] == "active"


_BASE_RECORD = TaskRecord(
    task_id="TASK-1",
    title="Task",
    status="open",
    priority="high",
    role=None,
    plan_id="plan-1",
    notes=None,
    assigned_by=None,
    branch=None,
    receipts=[],
    assignment_engineer="codex-1",
    assignment_manager="codex-4",
    assignment_note=None,
    assignment_branch=None,
    assigned_at=None,
    claim_agent=None,
    claim_status=None,
    claim_branch=None,
    claim_plan_id=None,
    claimed_at=None,
    released_at=None,
)


def _task_record(**overrides: object) -> TaskRecord:
    return replace(_BASE_RECORD, **overrides)


def test_compute_warnings_flags_missing_plan_for_open_task() -> None:
    record = _task_record(plan_id=None, status="open")
    warnings = tasks_report.compute_warnings([record])
    assert any("missing plan_id" in warning for warning in warnings)
