from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tools.agent import parallel_guard


@pytest.fixture()
def temp_guard_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path
    events = root / "_bus" / "events"
    claims = root / "_bus" / "claims"
    docs = root / "docs" / "automation"
    events.mkdir(parents=True, exist_ok=True)
    claims.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)

    consent_path = docs / "autonomy-consent.json"
    consent_path.write_text(
        json.dumps(
            {
                "parallel": {
                    "hard_window_seconds": 900,
                    "soft_window_seconds": 1800,
                    "stale_window_seconds": 3600,
                    "require_plan_claim": True,
                    "require_scan_receipt": True,
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(parallel_guard, "ROOT", root, raising=False)
    monkeypatch.setattr(parallel_guard, "EVENT_LOG", events / "events.jsonl", raising=False)
    monkeypatch.setattr(parallel_guard, "CLAIMS_DIR", claims, raising=False)
    monkeypatch.setattr(parallel_guard, "CONSENT_POLICY_PATH", consent_path, raising=False)
    return root


def _write_event(path: Path, agent_id: str, *, age_seconds: int, event: str = "handshake") -> None:
    now = datetime.now(timezone.utc)
    ts = (now - timedelta(seconds=age_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "agent_id": agent_id,
        "event": event,
        "summary": "hello",
        "ts": ts,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _write_claim(path: Path, *, agent_id: str, task_id: str, status: str = "active") -> None:
    payload = {
        "agent_id": agent_id,
        "task_id": task_id,
        "status": status,
        "claimed_at": "2025-10-05T12:00:00Z",
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_detect_parallel_state_none(temp_guard_env: Path) -> None:
    report = parallel_guard.detect_parallel_state("codex-1")
    assert report.severity == "none"
    assert report.requirements["session_boot"] is False


def test_detect_parallel_state_hard_due_to_claim(temp_guard_env: Path) -> None:
    claim_path = parallel_guard.CLAIMS_DIR / "QUEUE-001.json"
    _write_claim(claim_path, agent_id="codex-peer", task_id="QUEUE-001")
    report = parallel_guard.detect_parallel_state("codex-1")
    assert report.severity == "hard"
    assert report.requirements["plan_claim"] is True
    assert report.active_claims


def test_detect_parallel_state_soft_due_to_recent_event(temp_guard_env: Path) -> None:
    _write_event(parallel_guard.EVENT_LOG, "codex-peer", age_seconds=1200)
    report = parallel_guard.detect_parallel_state("codex-1")
    assert report.severity == "soft"
    assert "codex-peer" in report.soft_agents


def test_agent_has_active_claim(temp_guard_env: Path) -> None:
    claim_path = parallel_guard.CLAIMS_DIR / "QUEUE-002.json"
    _write_claim(claim_path, agent_id="codex-1", task_id="QUEUE-002")
    assert parallel_guard.agent_has_active_claim("codex-1") is True


def test_write_parallel_receipt(temp_guard_env: Path) -> None:
    report = parallel_guard.detect_parallel_state("codex-1")
    receipt = parallel_guard.write_parallel_receipt("codex-1", report)
    assert receipt.exists()
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert payload["agent_id"] == "codex-1"
    assert payload["severity"] == "none"
