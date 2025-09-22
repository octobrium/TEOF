from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.agent import authenticity_escalation as escalation


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _summary_payload(trust: float, *, status: str = "attention", steward: str | None = "codex-5") -> dict[str, object]:
    feed: dict[str, object] = {
        "feed_id": "demo",
        "trust_adjusted": trust,
        "status": status,
    }
    if steward is not None:
        feed["steward_id"] = steward
    return {
        "authenticity": {
            "primary_truth": {
                "feeds": [feed],
            }
        }
    }


def test_escalates_after_two_runs(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    auth_path = tmp_path / "auth.json"
    state_path = tmp_path / "state.json"
    receipt_path = tmp_path / "receipt.json"

    _write(summary_path, _summary_payload(0.55))
    _write(auth_path, {})

    result1 = escalation.process_authenticity(
        auth_json=auth_path,
        summary_json=summary_path,
        state_path=state_path,
        receipt_path=receipt_path,
        threshold=0.6,
        streak_required=2,
        manager="codex-4",
        plan_id=None,
        task_prefix="AUTH",
        auto_claim=False,
        dry_run=True,
    )
    assert result1["escalations"] == []
    state_data = json.loads(state_path.read_text(encoding="utf-8"))
    assert state_data["tiers"]["primary_truth"]["streak"] == 1

    result2 = escalation.process_authenticity(
        auth_json=auth_path,
        summary_json=summary_path,
        state_path=state_path,
        receipt_path=receipt_path,
        threshold=0.6,
        streak_required=2,
        manager="codex-4",
        plan_id=None,
        task_prefix="AUTH",
        auto_claim=False,
        dry_run=True,
    )
    assert len(result2["escalations"]) == 1
    record = result2["escalations"][0]
    assert record["tier"] == "primary_truth"
    assert record["steward_id"] == "codex-5"
    assert record["feed_ids"] == ["demo"]

    # Third run should not duplicate escalation while streak continues.
    result3 = escalation.process_authenticity(
        auth_json=auth_path,
        summary_json=summary_path,
        state_path=state_path,
        receipt_path=receipt_path,
        threshold=0.6,
        streak_required=2,
        manager="codex-4",
        plan_id=None,
        task_prefix="AUTH",
        auto_claim=False,
        dry_run=True,
    )
    assert result3["escalations"] == []


def test_resets_after_recovery(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    auth_path = tmp_path / "auth.json"
    state_path = tmp_path / "state.json"
    receipt_path = tmp_path / "receipt.json"

    _write(summary_path, _summary_payload(0.4))
    _write(auth_path, {})

    # trip streak 2 -> escalate once
    escalation.process_authenticity(
        auth_json=auth_path,
        summary_json=summary_path,
        state_path=state_path,
        receipt_path=receipt_path,
        threshold=0.6,
        streak_required=2,
        manager="codex-4",
        plan_id=None,
        task_prefix="AUTH",
        auto_claim=False,
        dry_run=True,
    )
    escalation.process_authenticity(
        auth_json=auth_path,
        summary_json=summary_path,
        state_path=state_path,
        receipt_path=receipt_path,
        threshold=0.6,
        streak_required=2,
        manager="codex-4",
        plan_id=None,
        task_prefix="AUTH",
        auto_claim=False,
        dry_run=True,
    )

    # recovery run resets streak and allows future alerts.
    _write(summary_path, _summary_payload(0.8, status="ok"))
    result = escalation.process_authenticity(
        auth_json=auth_path,
        summary_json=summary_path,
        state_path=state_path,
        receipt_path=receipt_path,
        threshold=0.6,
        streak_required=2,
        manager="codex-4",
        plan_id=None,
        task_prefix="AUTH",
        auto_claim=False,
        dry_run=True,
    )
    state_data = json.loads(state_path.read_text(encoding="utf-8"))
    assert state_data["tiers"]["primary_truth"]["streak"] == 0
    assert state_data["tiers"]["primary_truth"]["escalated"] == {}
    assert result["escalations"] == []

    # After recovery, degradation again should escalate after streak rebuild.
    _write(summary_path, _summary_payload(0.4))
    escalation.process_authenticity(
        auth_json=auth_path,
        summary_json=summary_path,
        state_path=state_path,
        receipt_path=receipt_path,
        threshold=0.6,
        streak_required=2,
        manager="codex-4",
        plan_id=None,
        task_prefix="AUTH",
        auto_claim=False,
        dry_run=True,
    )
    result_after = escalation.process_authenticity(
        auth_json=auth_path,
        summary_json=summary_path,
        state_path=state_path,
        receipt_path=receipt_path,
        threshold=0.6,
        streak_required=2,
        manager="codex-4",
        plan_id=None,
        task_prefix="AUTH",
        auto_claim=False,
        dry_run=True,
    )
    assert len(result_after["escalations"]) == 1


def test_ignores_unassigned_feeds(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    auth_path = tmp_path / "auth.json"
    state_path = tmp_path / "state.json"
    receipt_path = tmp_path / "receipt.json"

    _write(summary_path, _summary_payload(0.3, steward=None))
    _write(auth_path, {})

    escalation.process_authenticity(
        auth_json=auth_path,
        summary_json=summary_path,
        state_path=state_path,
        receipt_path=receipt_path,
        threshold=0.6,
        streak_required=2,
        manager="codex-4",
        plan_id=None,
        task_prefix="AUTH",
        auto_claim=False,
        dry_run=True,
    )
    result = escalation.process_authenticity(
        auth_json=auth_path,
        summary_json=summary_path,
        state_path=state_path,
        receipt_path=receipt_path,
        threshold=0.6,
        streak_required=2,
        manager="codex-4",
        plan_id=None,
        task_prefix="AUTH",
        auto_claim=False,
        dry_run=True,
    )
    assert result["escalations"] == []


def test_invokes_task_assign_when_not_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    summary_path = tmp_path / "summary.json"
    auth_path = tmp_path / "auth.json"
    state_path = tmp_path / "state.json"
    receipt_path = tmp_path / "receipt.json"

    _write(summary_path, _summary_payload(0.4))
    _write(auth_path, {})

    calls: list[list[str]] = []

    def fake_main(argv: list[str] | None = None) -> int:
        assert argv is not None
        calls.append(list(argv))
        return 0

    monkeypatch.setattr(escalation.task_assign, "main", fake_main)

    # Prime streak to 2
    escalation.process_authenticity(
        auth_json=auth_path,
        summary_json=summary_path,
        state_path=state_path,
        receipt_path=receipt_path,
        threshold=0.6,
        streak_required=2,
        manager="codex-4",
        plan_id="2025-09-23-authenticity-steward-alerts",
        task_prefix="AUTH",
        auto_claim=False,
        dry_run=False,
    )
    escalation.process_authenticity(
        auth_json=auth_path,
        summary_json=summary_path,
        state_path=state_path,
        receipt_path=receipt_path,
        threshold=0.6,
        streak_required=2,
        manager="codex-4",
        plan_id="2025-09-23-authenticity-steward-alerts",
        task_prefix="AUTH",
        auto_claim=False,
        dry_run=False,
    )

    assert calls, "expected task_assign to be invoked"
    argv = calls[0]
    assert "--task" in argv
    assert "--engineer" in argv and argv[argv.index("--engineer") + 1] == "codex-5"
    assert "--plan" in argv and argv[argv.index("--plan") + 1] == "2025-09-23-authenticity-steward-alerts"
    assert "--no-auto-claim" in argv
