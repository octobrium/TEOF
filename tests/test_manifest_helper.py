from __future__ import annotations

import json
from pathlib import Path

from tools.agent import manifest_helper


def _fake_git(responses, recorder=None):
    def runner(args):
        key = " ".join(args)
        if recorder is not None:
            recorder.append(args)
        if key not in responses:
            raise AssertionError(f"Unexpected git command: {args}")
        return responses[key]

    return runner


def _write_manifest(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_list_variants(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    monkeypatch.setattr(manifest_helper, "ROOT", root)
    monkeypatch.setattr(manifest_helper, "DEFAULT_MANIFEST", root / "AGENT_MANIFEST.json")
    monkeypatch.setattr(manifest_helper, "BACKUP_DIR", root / ".manifest_backups")

    _write_manifest(root / "AGENT_MANIFEST.json", "{\"agent_id\": \"base\"}")
    _write_manifest(root / "AGENT_MANIFEST.codex-1.json", "{}")
    _write_manifest(root / "AGENT_MANIFEST.codex-2.json", "{}")

    variants = manifest_helper.list_variants()
    assert variants == ["AGENT_MANIFEST.codex-1.json", "AGENT_MANIFEST.codex-2.json"]


def test_activate_creates_backup_and_switches(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    monkeypatch.setattr(manifest_helper, "ROOT", root)
    default_manifest = root / "AGENT_MANIFEST.json"
    backup_dir = root / ".manifest_backups"
    monkeypatch.setattr(manifest_helper, "DEFAULT_MANIFEST", default_manifest)
    monkeypatch.setattr(manifest_helper, "BACKUP_DIR", backup_dir)

    _write_manifest(default_manifest, "{\"agent_id\": \"base\"}")
    _write_manifest(root / "AGENT_MANIFEST.codex-9.json", "{\"agent_id\": \"codex-9\"}")

    manifest_helper.activate_variant("AGENT_MANIFEST.codex-9.json")

    updated = default_manifest.read_text(encoding="utf-8")
    assert "codex-9" in updated
    backups = list(backup_dir.glob("AGENT_MANIFEST.json.*"))
    assert len(backups) == 1


def test_restore_uses_latest_backup(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    default_manifest = root / "AGENT_MANIFEST.json"
    backup_dir = root / ".manifest_backups"
    monkeypatch.setattr(manifest_helper, "ROOT", root)
    monkeypatch.setattr(manifest_helper, "DEFAULT_MANIFEST", default_manifest)
    monkeypatch.setattr(manifest_helper, "BACKUP_DIR", backup_dir)

    _write_manifest(default_manifest, "{\"agent_id\": \"base\"}")
    backup_dir.mkdir()
    older = backup_dir / "AGENT_MANIFEST.json.1"
    newer = backup_dir / "AGENT_MANIFEST.json.2"
    _write_manifest(older, "{\"agent_id\": \"old\"}")
    _write_manifest(newer, "{\"agent_id\": \"new\"}")

    manifest_helper.restore_default()
    assert default_manifest.read_text(encoding="utf-8") == newer.read_text(encoding="utf-8")


def test_session_save_writes_manifest_and_metadata(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    monkeypatch.setattr(manifest_helper, "ROOT", root)
    monkeypatch.setattr(manifest_helper, "DEFAULT_MANIFEST", root / "AGENT_MANIFEST.json")
    monkeypatch.setattr(manifest_helper, "SESSION_DIR", root / ".sessions")
    monkeypatch.setattr(manifest_helper, "BACKUP_DIR", root / ".manifest_backups")

    _write_manifest(manifest_helper.DEFAULT_MANIFEST, "{\"agent_id\": \"codex-2\"}")

    responses = {
        "status --porcelain": "",
        "rev-parse --abbrev-ref HEAD": "agent/codex-2/work",
        "rev-parse HEAD": "abc123",
    }
    monkeypatch.setattr(manifest_helper, "_git", _fake_git(responses))

    manifest_helper.save_session("daily")

    session_dir = manifest_helper.SESSION_DIR / "daily"
    assert session_dir.exists()
    saved_manifest = session_dir / "AGENT_MANIFEST.json"
    assert saved_manifest.read_text(encoding="utf-8") == manifest_helper.DEFAULT_MANIFEST.read_text(encoding="utf-8")
    metadata = json.loads((session_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["branch"] == "agent/codex-2/work"
    assert metadata["agent_id"] == "codex-2"


def test_session_restore_checks_out_branch(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    monkeypatch.setattr(manifest_helper, "ROOT", root)
    monkeypatch.setattr(manifest_helper, "DEFAULT_MANIFEST", root / "AGENT_MANIFEST.json")
    monkeypatch.setattr(manifest_helper, "SESSION_DIR", root / ".sessions")
    monkeypatch.setattr(manifest_helper, "BACKUP_DIR", root / ".manifest_backups")

    current_manifest = manifest_helper.DEFAULT_MANIFEST
    _write_manifest(current_manifest, "{\"agent_id\": \"current\"}")

    session_dir = manifest_helper.SESSION_DIR / "focus"
    session_dir.mkdir(parents=True)
    _write_manifest(session_dir / "AGENT_MANIFEST.json", "{\"agent_id\": \"saved\"}")
    (session_dir / "metadata.json").write_text(
        json.dumps({
            "label": "focus",
            "agent_id": "codex-2",
            "branch": "agent/codex-2/work",
            "commit": "abc123",
            "created": "2025-09-19T00:00:00Z",
        }),
        encoding="utf-8",
    )

    commands = []
    responses = {
        "status --porcelain": "",
        "checkout agent/codex-2/work": "Switched",
    }
    monkeypatch.setattr(manifest_helper, "_git", _fake_git(responses, recorder=commands))

    manifest_helper.restore_session("focus")

    assert commands[0] == ["status", "--porcelain"]
    assert commands[1] == ["checkout", "agent/codex-2/work"]
    restored = manifest_helper.DEFAULT_MANIFEST.read_text(encoding="utf-8")
    assert "saved" in restored


def test_session_list_returns_metadata(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    monkeypatch.setattr(manifest_helper, "SESSION_DIR", root / ".sessions")
    session_dir = manifest_helper.SESSION_DIR / "alpha"
    session_dir.mkdir(parents=True)
    (session_dir / "metadata.json").write_text(
        json.dumps({"label": "alpha", "branch": "agent/codex-2/dev", "created": "2025-09-19T00:00:00Z"}),
        encoding="utf-8",
    )

    sessions = manifest_helper.list_sessions()
    assert sessions and sessions[0]["label"] == "alpha"
