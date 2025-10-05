from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tools.agent import session_guard


ISO_FMT = session_guard.ISO_FMT


def _configure(tmp_path: Path, monkeypatch) -> tuple[Path, Path, Path, Path]:
    root = tmp_path / "repo"
    root.mkdir()
    manifest = root / "AGENT_MANIFEST.json"
    manifest.write_text(json.dumps({"agent_id": "codex-test"}), encoding="utf-8")

    session_dir = root / "_report" / "session"
    agent_dir = root / "_report" / "agent"

    monkeypatch.setattr(session_guard, "ROOT", root)
    monkeypatch.setattr(session_guard, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(session_guard, "SESSION_DIR", session_dir)
    monkeypatch.setattr(session_guard, "AGENT_REPORT_DIR", agent_dir)
    monkeypatch.delenv("TEOF_SESSION_GUARD_DISABLED", raising=False)

    return root, manifest, session_dir, agent_dir


def test_resolve_agent_defaults_to_manifest(tmp_path: Path, monkeypatch) -> None:
    _, _, _, _ = _configure(tmp_path, monkeypatch)
    assert session_guard.resolve_agent_id(None) == "codex-test"


def test_resolve_agent_mismatch_raises(tmp_path: Path, monkeypatch) -> None:
    _, _, _, _ = _configure(tmp_path, monkeypatch)
    with pytest.raises(SystemExit):
        session_guard.resolve_agent_id("codex-other")


def test_ensure_recent_session_missing_receipt(tmp_path: Path, monkeypatch) -> None:
    _, _, session_dir, agent_dir = _configure(tmp_path, monkeypatch)
    agent_id = "codex-test"

    with pytest.raises(SystemExit) as exc:
        session_guard.ensure_recent_session(agent_id)
    assert "session guard" in str(exc.value)

    events = agent_dir / agent_id / "session_guard" / "events.jsonl"
    assert events.exists()
    contents = events.read_text(encoding="utf-8").splitlines()
    assert any("session_missing" in line for line in contents)


def test_ensure_recent_session_stale(tmp_path: Path, monkeypatch) -> None:
    _, _, session_dir, agent_dir = _configure(tmp_path, monkeypatch)
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
    _, _, session_dir, _ = _configure(tmp_path, monkeypatch)
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
