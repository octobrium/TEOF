from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.agent import manifest_helper


def test_activate_variant_accepts_slug(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path
    default = root / "AGENT_MANIFEST.json"
    backup_dir = root / ".manifest_backups"
    session_dir = root / ".manifest_sessions"
    variant = root / "AGENT_MANIFEST.codex-4.json"

    default.write_text(json.dumps({"agent_id": "claude-coding-1"}), encoding="utf-8")
    variant.write_text(json.dumps({"agent_id": "codex-4"}), encoding="utf-8")

    monkeypatch.setattr(manifest_helper, "ROOT", root)
    monkeypatch.setattr(manifest_helper, "DEFAULT_MANIFEST", default)
    monkeypatch.setattr(manifest_helper, "BACKUP_DIR", backup_dir)
    monkeypatch.setattr(manifest_helper, "SESSION_DIR", session_dir)

    activated = manifest_helper.activate_variant("codex-4", backup=False)

    assert activated == variant
    assert json.loads(default.read_text(encoding="utf-8")) == {"agent_id": "codex-4"}
