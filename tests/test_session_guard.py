from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tools.agent import session_guard


ISO_FMT = session_guard.ISO_FMT


def _configure(tmp_path: Path, monkeypatch) -> tuple[Path, Path, Path, Path, Path]:
    root = tmp_path / "repo"
    root.mkdir()
    manifest = root / "AGENT_MANIFEST.json"
    manifest.write_text(json.dumps({"agent_id": "codex-test"}), encoding="utf-8")

    session_dir = root / "_report" / "session"
    agent_dir = root / "_report" / "agent"
    memory_dir = root / "memory"
    memory_dir.mkdir()
    (memory_dir / "log.jsonl").write_text(
        json.dumps({"ts": datetime.now(timezone.utc).strftime(ISO_FMT), "summary": "bootstrap"}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(session_guard, "ROOT", root)
    monkeypatch.setattr(session_guard, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(session_guard, "SESSION_DIR", session_dir)
    monkeypatch.setattr(session_guard, "AGENT_REPORT_DIR", agent_dir)
    monkeypatch.setattr(session_guard, "MEMORY_LOG_PATH", memory_dir / "log.jsonl")
    monkeypatch.delenv("TEOF_SESSION_GUARD_DISABLED", raising=False)

    return root, manifest, session_dir, agent_dir, memory_dir


def test_resolve_agent_defaults_to_manifest(tmp_path: Path, monkeypatch) -> None:
    _configure(tmp_path, monkeypatch)
    assert session_guard.resolve_agent_id(None) == "codex-test"


def test_resolve_agent_mismatch_raises(tmp_path: Path, monkeypatch) -> None:
    _configure(tmp_path, monkeypatch)
    with pytest.raises(SystemExit):
        session_guard.resolve_agent_id("codex-other")


def test_ensure_recent_session_missing_receipt(tmp_path: Path, monkeypatch) -> None:
    _, _, session_dir, agent_dir, _ = _configure(tmp_path, monkeypatch)
    agent_id = "codex-test"

    with pytest.raises(SystemExit) as exc:
        session_guard.ensure_recent_session(agent_id)
    assert "session guard" in str(exc.value)

    events = agent_dir / agent_id / "session_guard" / "events.jsonl"
    assert events.exists()
    contents = events.read_text(encoding="utf-8").splitlines()
    assert any("session_missing" in line for line in contents)


def test_ensure_recent_session_stale(tmp_path: Path, monkeypatch) -> None:
    _, _, session_dir, agent_dir, _ = _configure(tmp_path, monkeypatch)
    agent_id = "codex-test"

    receipt_dir = session_dir / agent_id
    receipt_dir.mkdir(parents=True, exist_ok=True)
    tail_path = receipt_dir / "manager-report-tail.txt"
    stale_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime(ISO_FMT)
    tail_path.write_text(
        "# manager-report tail\n"
        "# source=_bus/messages/manager-report.jsonl\n"
        f"# captured_at={stale_ts}\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit):
        session_guard.ensure_recent_session(agent_id, max_age_seconds=600)

    # Override should log but not raise
    session_guard.ensure_recent_session(agent_id, allow_stale=True, max_age_seconds=600)

    events = agent_dir / agent_id / "session_guard" / "events.jsonl"
    lines = events.read_text(encoding="utf-8").splitlines()
    assert any("session_stale" in line for line in lines)
    assert any("session_override" in line for line in lines)


def test_ensure_recent_session_recent_ok(tmp_path: Path, monkeypatch) -> None:
    _, _, session_dir, _, _ = _configure(tmp_path, monkeypatch)
    agent_id = "codex-test"

    receipt_dir = session_dir / agent_id
    receipt_dir.mkdir(parents=True, exist_ok=True)
    tail_path = receipt_dir / "manager-report-tail.txt"
    fresh_ts = datetime.now(timezone.utc).strftime(ISO_FMT)
    tail_path.write_text(
        "# manager-report tail\n"
        "# source=_bus/messages/manager-report.jsonl\n"
        f"# captured_at={fresh_ts}\n",
        encoding="utf-8",
    )

    session_guard.ensure_recent_session(agent_id, max_age_seconds=600)


def test_record_memory_observation_writes_latest_entry(tmp_path: Path, monkeypatch) -> None:
    _, _, _, agent_dir, memory_dir = _configure(tmp_path, monkeypatch)
    log_path = memory_dir / "log.jsonl"
    log_path.write_text(
        '\n'.join(
            [
                json.dumps({"ts": "2025-11-08T21:00:00Z", "summary": "older"}),
                json.dumps({"ts": "2025-11-08T21:30:00Z", "summary": "newer", "ref": "PR-1"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    out_path = session_guard.record_memory_observation("codex-test", memory_log=log_path, context="dna")
    data = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert data[-1]["memory_entry"]["summary"] == "newer"
    assert data[-1]["memory_entry"]["ref"] == "PR-1"

    events = agent_dir / "codex-test" / "memory_guard" / "events.jsonl"
    assert not events.exists()  # logging only occurs on errors


def test_ensure_recent_memory_observation_catches_missing(tmp_path: Path, monkeypatch) -> None:
    _, _, _, agent_dir, _ = _configure(tmp_path, monkeypatch)
    with pytest.raises(SystemExit):
        session_guard.ensure_recent_memory_observation("codex-test", context="dna")

    events = agent_dir / "codex-test" / "memory_guard" / "events.jsonl"
    assert events.exists()
    assert "memory_missing" in events.read_text(encoding="utf-8")


def test_ensure_recent_memory_observation_stale(tmp_path: Path, monkeypatch) -> None:
    _, _, _, _, memory_dir = _configure(tmp_path, monkeypatch)
    log_path = memory_dir / "log.jsonl"
    log_path.write_text(json.dumps({"ts": "2025-11-08T21:00:00Z", "summary": "ok"}) + "\n", encoding="utf-8")
    checks = session_guard.record_memory_observation("codex-test", memory_log=log_path, context="dna")

    # Overwrite timestamp to simulate staleness
    payloads = [json.loads(line) for line in checks.read_text(encoding="utf-8").splitlines() if line.strip()]
    payloads[-1]["ts"] = "2024-01-01T00:00:00Z"
    checks.write_text("\n".join(json.dumps(p, sort_keys=True) for p in payloads) + "\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        session_guard.ensure_recent_memory_observation("codex-test", context="dna", max_age_seconds=60)

    session_guard.ensure_recent_memory_observation(
        "codex-test",
        context="dna",
        max_age_seconds=60,
        allow_stale=True,
    )
