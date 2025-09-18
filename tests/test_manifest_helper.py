from __future__ import annotations

from pathlib import Path

from tools.agent import manifest_helper


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
