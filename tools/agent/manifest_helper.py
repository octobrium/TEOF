#!/usr/bin/env python3
"""Manage agent manifest variants and session swaps."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "AGENT_MANIFEST.json"
BACKUP_DIR = ROOT / ".manifest_backups"
SESSION_DIR = ROOT / ".manifest_sessions"


def _iter_variants() -> Iterable[Path]:
    for path in ROOT.glob("AGENT_MANIFEST.*.json"):
        if path.name == DEFAULT_MANIFEST.name:
            continue
        yield path


def _backup_manifest() -> None:
    if not DEFAULT_MANIFEST.exists():
        return
    BACKUP_DIR.mkdir(exist_ok=True)
    backup_path = BACKUP_DIR / f"{DEFAULT_MANIFEST.name}.{DEFAULT_MANIFEST.stat().st_mtime_ns}"
    shutil.copy2(DEFAULT_MANIFEST, backup_path)


def list_variants() -> list[str]:
    variants = [p.name for p in sorted(_iter_variants())]
    return variants


def activate_variant(name: str, backup: bool = True) -> Path:
    target = ROOT / name
    if not target.exists():
        raise SystemExit(f"variant {name} not found")
    if backup and DEFAULT_MANIFEST.exists():
        _backup_manifest()
    shutil.copy2(target, DEFAULT_MANIFEST)
    return target


def restore_default() -> None:
    backups = sorted(BACKUP_DIR.glob("AGENT_MANIFEST.json.*"))
    if not backups:
        raise SystemExit("no backups available")
    latest = backups[-1]
    shutil.copy2(latest, DEFAULT_MANIFEST)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage agent manifest variants")
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="List available manifest variants")
    list_cmd.set_defaults(func=cmd_list)

    activate = sub.add_parser("activate", help="Activate a manifest variant")
    activate.add_argument("name", help="Variant filename (AGENT_MANIFEST.<id>.json)")
    activate.add_argument("--no-backup", action="store_true", help="Skip backing up current manifest")
    activate.set_defaults(func=cmd_activate)

    restore = sub.add_parser("restore", help="Restore the most recent backup")
    restore.set_defaults(func=cmd_restore)

    session_save = sub.add_parser("session-save", help="Snapshot manifest + branch for later restore")
    session_save.add_argument("label", help="Name for the saved session")
    session_save.add_argument("--allow-dirty", action="store_true", help="Allow saving when working tree has changes")
    session_save.add_argument("--force", action="store_true", help="Overwrite existing session with same label")
    session_save.set_defaults(func=cmd_session_save)

    session_restore = sub.add_parser("session-restore", help="Restore manifest and branch from saved session")
    session_restore.add_argument("label", help="Session label to restore")
    session_restore.add_argument("--manifest-only", action="store_true", help="Restore manifest without checking out branch")
    session_restore.add_argument("--allow-dirty", action="store_true", help="Skip dirty working tree guard")
    session_restore.add_argument("--no-backup", action="store_true", help="Skip backing up current manifest before restoring")
    session_restore.set_defaults(func=cmd_session_restore)

    session_list = sub.add_parser("session-list", help="List saved sessions")
    session_list.set_defaults(func=cmd_session_list)

    session_delete = sub.add_parser("session-delete", help="Delete a saved session")
    session_delete.add_argument("label", help="Session label to delete")
    session_delete.set_defaults(func=cmd_session_delete)

    return parser


def cmd_list(_: argparse.Namespace) -> int:
    variants = list_variants()
    if not variants:
        print("No manifest variants found.")
        return 0
    for name in variants:
        print(name)
    return 0


def cmd_activate(args: argparse.Namespace) -> int:
    activate_variant(args.name, backup=not args.no_backup)
    print(f"Activated {args.name}")
    return 0


def cmd_restore(_: argparse.Namespace) -> int:
    restore_default()
    print("Restored manifest from latest backup")
    return 0


def _git(args: Sequence[str]) -> str:
    result = subprocess.run([
        "git",
        *args,
    ], cwd=ROOT, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _read_manifest_agent() -> str | None:
    if not DEFAULT_MANIFEST.exists():
        return None
    try:
        data = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    agent = data.get("agent_id")
    if isinstance(agent, str) and agent.strip():
        return agent.strip()
    return None


def save_session(
    label: str,
    *,
    allow_dirty: bool = False,
    force: bool = False,
) -> Path:
    label = label.strip()
    if not label:
        raise SystemExit("session label must be non-empty")
    if not DEFAULT_MANIFEST.exists():
        raise SystemExit("AGENT_MANIFEST.json missing; run onboarding steps first")

    status = _git(["status", "--porcelain"])
    if status and not allow_dirty:
        raise SystemExit("working tree dirty; commit/stash or pass --allow-dirty")

    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"])
    commit = _git(["rev-parse", "HEAD"])
    agent_id = _read_manifest_agent() or "unknown"

    session_dir = SESSION_DIR / label
    if session_dir.exists():
        if not force:
            raise SystemExit(f"session '{label}' already exists; use --force to overwrite")
        shutil.rmtree(session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(DEFAULT_MANIFEST, session_dir / DEFAULT_MANIFEST.name)
    metadata = {
        "label": label,
        "agent_id": agent_id,
        "branch": branch,
        "commit": commit,
        "created": datetime.now(timezone.utc).isoformat(),
    }
    (session_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return session_dir


def _load_session(label: str) -> tuple[Path, dict[str, str]]:
    session_dir = SESSION_DIR / label
    if not session_dir.exists():
        raise SystemExit(f"session '{label}' not found")
    metadata_path = session_dir / "metadata.json"
    if not metadata_path.exists():
        raise SystemExit(f"session '{label}' missing metadata.json")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"session '{label}' metadata invalid: {exc}") from exc
    return session_dir, metadata


def restore_session(
    label: str,
    *,
    manifest_only: bool = False,
    allow_dirty: bool = False,
    backup_manifest: bool = True,
) -> None:
    session_dir, metadata = _load_session(label)

    status = _git(["status", "--porcelain"])
    if status and not allow_dirty:
        raise SystemExit("working tree dirty; commit/stash changes or pass --allow-dirty")

    if not manifest_only:
        branch = metadata.get("branch")
        if not branch:
            raise SystemExit(f"session '{label}' missing branch information")
        _git(["checkout", branch])

    session_manifest = session_dir / DEFAULT_MANIFEST.name
    if not session_manifest.exists():
        raise SystemExit(f"session '{label}' missing manifest copy")
    if backup_manifest:
        _backup_manifest()
    shutil.copy2(session_manifest, DEFAULT_MANIFEST)


def list_sessions() -> list[dict[str, str]]:
    sessions: list[dict[str, str]] = []
    if not SESSION_DIR.exists():
        return sessions
    for path in sorted(SESSION_DIR.iterdir()):
        if not path.is_dir():
            continue
        metadata_path = path / "metadata.json"
        if not metadata_path.exists():
            continue
        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        data["label"] = data.get("label") or path.name
        sessions.append(data)
    return sessions


def delete_session(label: str) -> None:
    session_dir = SESSION_DIR / label
    if not session_dir.exists():
        raise SystemExit(f"session '{label}' not found")
    shutil.rmtree(session_dir)


def cmd_session_save(args: argparse.Namespace) -> int:
    save_session(args.label, allow_dirty=args.allow_dirty, force=args.force)
    print(f"Saved session '{args.label}'")
    return 0


def cmd_session_restore(args: argparse.Namespace) -> int:
    restore_session(
        args.label,
        manifest_only=args.manifest_only,
        allow_dirty=args.allow_dirty,
        backup_manifest=not args.no_backup,
    )
    print(f"Restored session '{args.label}'")
    return 0


def cmd_session_list(_: argparse.Namespace) -> int:
    sessions = list_sessions()
    if not sessions:
        print("No saved sessions found.")
        return 0
    for entry in sessions:
        created = entry.get("created", "unknown")
        branch = entry.get("branch", "-")
        agent = entry.get("agent_id", "-")
        label = entry.get("label", "?")
        print(f"{label}: branch={branch} agent={agent} created={created}")
    return 0


def cmd_session_delete(args: argparse.Namespace) -> int:
    delete_session(args.label)
    print(f"Deleted session '{args.label}'")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
