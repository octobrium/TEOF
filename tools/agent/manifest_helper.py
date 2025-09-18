#!/usr/bin/env python3
"""Manage agent manifest variants (list/swap/restore)."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "AGENT_MANIFEST.json"
BACKUP_DIR = ROOT / ".manifest_backups"


def _iter_variants() -> Iterable[Path]:
    for path in ROOT.glob("AGENT_MANIFEST.*.json"):
        if path.name == DEFAULT_MANIFEST.name:
            continue
        yield path


def list_variants() -> list[str]:
    variants = [p.name for p in sorted(_iter_variants())]
    return variants


def activate_variant(name: str, backup: bool = True) -> Path:
    target = ROOT / name
    if not target.exists():
        raise SystemExit(f"variant {name} not found")
    if backup and DEFAULT_MANIFEST.exists():
        BACKUP_DIR.mkdir(exist_ok=True)
        backup_path = BACKUP_DIR / f"{DEFAULT_MANIFEST.name}.{DEFAULT_MANIFEST.stat().st_mtime_ns}"
        shutil.copy2(DEFAULT_MANIFEST, backup_path)
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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
