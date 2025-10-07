from __future__ import annotations

import subprocess
import json
from pathlib import Path
from typing import List

import pytest

from tools.agent import batch_refinement


@pytest.fixture(autouse=True)
def stub_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_backlog(threshold: int, candidate_limit: int):
        payload = {"metrics": {"pending_threshold_breached": False}, "receipt_path": "_report/usage/backlog-health/test.json"}
        return payload, False

    def fake_confidence(warn_threshold: float, window: int, min_count: int, alert_ratio: float, report_dir: Path):
        payload = {"report": {"alerts": [], "generated_at": "2025-10-07T00:00:00Z"}, "report_path": "_report/usage/confidence-watch/test.json"}
        return payload, False

    monkeypatch.setattr(batch_refinement, "_run_backlog_health_guard", fake_backlog)
    monkeypatch.setattr(batch_refinement, "_run_confidence_watch_guard", fake_confidence)


class DummyResult:
    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode


def test_batch_refinement_runs_components(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: List[List[str]] = []

    def fake_run(cmd, cwd=None):
        calls.append(cmd)
        return DummyResult(0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    hygiene_called = {}

    usage_dir = tmp_path / "usage"
    monkeypatch.setattr(batch_refinement.receipts_hygiene, "DEFAULT_USAGE_DIR", usage_dir)

    def fake_hygiene(**kwargs):
        hygiene_called["kwargs"] = kwargs
        return {"metrics": {"plans_missing_receipts": 0}}

    monkeypatch.setattr(batch_refinement.receipts_hygiene, "run_hygiene", fake_hygiene)

    def fake_load_claim(task):
        return {"task_id": task, "agent_id": "codex-1", "status": "active"}

    monkeypatch.setattr(batch_refinement.session_brief, "load_claim", fake_load_claim)

    preset_calls = {}

    def fake_preset(agent_id, task, claim, output=None):
        preset_calls["agent"] = agent_id
        preset_calls["task"] = task
        preset_calls["claim"] = claim
        preset_calls["output"] = output
        preset_calls["receipt"] = "_report/session/codex-1/session_brief/test.json"
        return {"summary": "pass", "receipt_path": preset_calls["receipt"]}

    monkeypatch.setattr(batch_refinement.session_brief, "_run_operator_preset", fake_preset)

    manifest = tmp_path / "AGENT_MANIFEST.json"
    manifest.write_text('{"agent_id": "codex-1"}', encoding="utf-8")
    monkeypatch.setattr(batch_refinement, "MANIFEST_PATH", manifest)

    def fake_task_sync():
        return ["QUEUE-999: open -> done"]

    monkeypatch.setattr(batch_refinement.task_sync, "sync_tasks", fake_task_sync)

    monkeypatch.setattr(batch_refinement.autonomy_status, "ROOT", tmp_path)
    monkeypatch.setattr(
        batch_refinement.autonomy_status,
        "HYGIENE_SUMMARY",
        tmp_path / "_report" / "usage" / "receipts-hygiene-summary.json",
    )
    monkeypatch.setattr(
        batch_refinement.autonomy_status,
        "BATCH_DIR",
        tmp_path / "_report" / "usage" / "batch-refinement",
    )

    def fake_load_hygiene():
        return {"metrics": {"plans_total": 1}}

    def fake_load_logs(limit=None):
        return [
            {
                "generated_at": "20250101T000000Z",
                "operator_preset": {"summary": "pass"},
                "agent": "codex-1",
                "_path": tmp_path / "_report" / "usage" / "batch-refinement" / "existing.json",
            }
        ]

    def fake_summarise(hygiene, logs):
        return {
            "hygiene": {"plans_total": hygiene.get("metrics", {}).get("plans_total")},
            "batch_logs": {"entries": len(logs), "warn_count": 0, "fail_count": 0},
            "top_slow_plans": [],
        }

    monkeypatch.setattr(batch_refinement.autonomy_status, "load_hygiene", fake_load_hygiene)
    monkeypatch.setattr(batch_refinement.autonomy_status, "load_batch_logs", fake_load_logs)
    monkeypatch.setattr(batch_refinement.autonomy_status, "summarise", fake_summarise)

    heartbeat_called = {}

    def fake_heartbeat(agent_id, summary, extras=None, dry_run=False):
        heartbeat_called["agent"] = agent_id
        heartbeat_called["summary"] = summary
        heartbeat_called["extras"] = extras
        payload = {"agent_id": agent_id, "summary": summary, "extras": extras or {}}
        return payload

    monkeypatch.setattr(batch_refinement.heartbeat, "emit_status", fake_heartbeat)

    def fake_latency(**kwargs):
        return {"alerts": [], "receipt_path": None}

    monkeypatch.setattr(batch_refinement.autonomy_latency, "check_latency", fake_latency)

    log_dir = tmp_path / "logs"

    result = batch_refinement.run_batch(
        task="QUEUE-999",
        agent=None,
        pytest_args=["-k", "test_stub"],
        quiet=True,
        output=None,
        log_dir=log_dir,
        fail_on_missing=True,
        max_plan_latency=123.0,
        latency_threshold=3600.0,
        latency_warn_threshold=None,
        latency_fail_threshold=None,
        latency_dry_run=True,
    )

    assert calls[0][:3] == [batch_refinement.sys.executable, "-m", "pytest"]
    assert "-k" in calls[0]
    assert hygiene_called["kwargs"]["quiet"] is True
    assert preset_calls["agent"] == "codex-1"
    assert preset_calls["task"] == "QUEUE-999"
    assert result["receipts_hygiene"]["metrics"]["plans_missing_receipts"] == 0
    assert hygiene_called["kwargs"]["fail_on_missing"] is True
    assert hygiene_called["kwargs"]["max_plan_latency"] == 123.0
    assert hygiene_called["kwargs"]["warn_plan_latency"] == batch_refinement.receipts_hygiene.DEFAULT_WARN_THRESHOLD
    assert hygiene_called["kwargs"]["fail_plan_latency"] == batch_refinement.receipts_hygiene.DEFAULT_FAIL_THRESHOLD
    assert result["task_sync"]["changes"]
    autonomy_receipt = tmp_path / "_report" / "usage" / "autonomy-status.json"
    assert autonomy_receipt.exists()
    assert result["autonomy_status"]["summary"]["batch_logs"]["entries"] >= 1
    assert result["autonomy_status"]["receipt_path"].endswith("autonomy-status.json")
    log_path = Path(result["log_path"])
    if not log_path.is_absolute():
        log_path = (batch_refinement.ROOT / log_path).resolve()
    assert log_path.exists()
    data = json.loads(log_path.read_text(encoding="utf-8"))
    assert data["task"] == "QUEUE-999"
    assert data["agent"] == "codex-1"
    assert data["operator_preset"]["receipt_path"] == preset_calls["receipt"]
    assert data["task_sync_changes"]
    assert data["autonomy_status_receipt"].endswith("autonomy-status.json")
    assert result["backlog_health"]["metrics"]["pending_threshold_breached"] is False
    assert result["confidence_watch"]["report"]["alerts"] == []
    assert "batch_summary" in data
    assert heartbeat_called["agent"] == "codex-1"
    assert "QUEUE-999" in heartbeat_called["summary"]
    assert heartbeat_called["extras"]["batch_log"].endswith(".json")
    assert result["heartbeat"]["agent_id"] == "codex-1"
    assert result["latency_alerts"] == []
    summary_info = result.get("batch_summary")
    assert summary_info is not None
    summary_path = Path(summary_info["path"])
    if not summary_path.is_absolute():
        summary_path = (batch_refinement.ROOT / summary_path).resolve()
    assert summary_path.exists()
    summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary_payload["total_runs"] >= 1
    assert "latest_log" in summary_payload


def test_batch_refinement_guard_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: DummyResult(0))
    monkeypatch.setattr(batch_refinement.receipts_hygiene, "run_hygiene", lambda **k: {"metrics": {}})
    monkeypatch.setattr(batch_refinement.receipts_hygiene, "DEFAULT_USAGE_DIR", tmp_path / "usage")
    monkeypatch.setattr(batch_refinement.session_brief, "load_claim", lambda task: {})
    monkeypatch.setattr(batch_refinement.session_brief, "_run_operator_preset", lambda *a, **k: {"summary": "pass", "receipt_path": "r"})
    manifest = tmp_path / "AGENT_MANIFEST.json"
    manifest.write_text('{"agent_id": "codex-1"}', encoding="utf-8")
    monkeypatch.setattr(batch_refinement, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(batch_refinement.task_sync, "sync_tasks", lambda: [])
    monkeypatch.setattr(batch_refinement.autonomy_status, "ROOT", tmp_path)
    monkeypatch.setattr(batch_refinement.autonomy_status, "load_hygiene", lambda: {})
    monkeypatch.setattr(batch_refinement.autonomy_status, "load_batch_logs", lambda: [])
    monkeypatch.setattr(
        batch_refinement.autonomy_status,
        "summarise",
        lambda hygiene, logs: {"batch_logs": {"entries": 0, "warn_count": 0, "fail_count": 0}},
    )
    monkeypatch.setattr(batch_refinement.autonomy_latency, "check_latency", lambda **k: {"alerts": [], "receipt_path": None})

    def fail_backlog(threshold: int, candidate_limit: int):
        return {"metrics": {"pending_threshold_breached": True}, "receipt_path": "_report/usage/backlog-health/fail.json"}, True

    monkeypatch.setattr(batch_refinement, "_run_backlog_health_guard", fail_backlog)

    with pytest.raises(SystemExit) as exc:
        batch_refinement.run_batch(
            task="QUEUE-123",
            agent=None,
            pytest_args=["-q"],
            quiet=True,
            output=None,
            log_dir=tmp_path / "logs",
        )
    assert "backlog health guard breached" in str(exc.value)


def test_batch_refinement_requires_agent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: DummyResult(0))
    monkeypatch.setattr(batch_refinement.receipts_hygiene, "run_hygiene", lambda **_: {})
    monkeypatch.setattr(batch_refinement.receipts_hygiene, "DEFAULT_USAGE_DIR", tmp_path / "usage")
    monkeypatch.setattr(batch_refinement.session_brief, "load_claim", lambda task: None)
    monkeypatch.setattr(batch_refinement.session_brief, "_run_operator_preset", lambda *a, **k: {})
    monkeypatch.setattr(batch_refinement, "MANIFEST_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(batch_refinement.heartbeat, "emit_status", lambda *a, **k: {})
    monkeypatch.setattr(batch_refinement.autonomy_latency, "check_latency", lambda **k: {"alerts": [], "receipt_path": None})

    with pytest.raises(SystemExit):
        batch_refinement.run_batch(
            task="QUEUE-001",
            agent=None,
            pytest_args=[],
            quiet=True,
            output=None,
        )


def test_batch_refinement_main_propagates_pytest_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fail_run(cmd, cwd=None):
        return DummyResult(1)

    monkeypatch.setattr(subprocess, "run", fail_run)
    hygiene_kwargs = {}

    def fake_hygiene(**kwargs):
        hygiene_kwargs.update(kwargs)
        return {}

    monkeypatch.setattr(batch_refinement.receipts_hygiene, "run_hygiene", fake_hygiene)
    monkeypatch.setattr(batch_refinement.receipts_hygiene, "DEFAULT_USAGE_DIR", tmp_path / "usage")
    monkeypatch.setattr(batch_refinement.session_brief, "load_claim", lambda task: None)
    monkeypatch.setattr(batch_refinement.session_brief, "_run_operator_preset", lambda *a, **k: {})
    monkeypatch.setattr(batch_refinement, "MANIFEST_PATH", tmp_path / "AGENT_MANIFEST.json")
    (tmp_path / "AGENT_MANIFEST.json").write_text('{"agent_id": "codex-1"}', encoding="utf-8")
    monkeypatch.setattr(batch_refinement.heartbeat, "emit_status", lambda *a, **k: {})
    monkeypatch.setattr(batch_refinement.autonomy_latency, "check_latency", lambda **k: {"alerts": [], "receipt_path": None})

    with pytest.raises(SystemExit) as exc:
        batch_refinement.main([
            "--task",
            "QUEUE-101",
            "--quiet",
            "--fail-on-missing",
            "--max-plan-latency",
            "45",
        ])
    assert "pytest failed" in str(exc.value)


def test_batch_refinement_main_passes_hygiene_flags(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: DummyResult(0))
    hygiene_kwargs = {}

    def fake_hygiene(**kwargs):
        hygiene_kwargs.update(kwargs)
        return {}

    monkeypatch.setattr(batch_refinement.receipts_hygiene, "run_hygiene", fake_hygiene)
    monkeypatch.setattr(batch_refinement.receipts_hygiene, "DEFAULT_USAGE_DIR", tmp_path / "usage")
    monkeypatch.setattr(batch_refinement.session_brief, "load_claim", lambda task: {})
    monkeypatch.setattr(batch_refinement.session_brief, "_run_operator_preset", lambda *a, **k: {"summary": "pass", "receipt_path": "r"})
    manifest = tmp_path / "AGENT_MANIFEST.json"
    manifest.write_text('{"agent_id": "codex-1"}', encoding="utf-8")
    monkeypatch.setattr(batch_refinement, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(batch_refinement.heartbeat, "emit_status", lambda *a, **k: {})
    monkeypatch.setattr(batch_refinement.autonomy_latency, "check_latency", lambda **k: {"alerts": [], "receipt_path": None})

    result = batch_refinement.main([
        "--task",
        "QUEUE-555",
        "--fail-on-missing",
        "--max-plan-latency",
        "30",
        "--quiet",
        "--latency-threshold",
        "3600",
        "--latency-dry-run",
    ])
    assert result == 0
    assert hygiene_kwargs["fail_on_missing"] is True
    assert hygiene_kwargs["max_plan_latency"] == 30.0
    assert "warn_plan_latency" in hygiene_kwargs
    assert "fail_plan_latency" in hygiene_kwargs
