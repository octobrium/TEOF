#!/usr/bin/env python3
"""Ensure guard tier manifest obeys Pattern C ordering."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "governance" / "guard-tiers.json"
TIER_ORDER = {"tactical": 0, "operational": 1, "core": 2}


def load_manifest() -> dict:
    if not MANIFEST.exists():
        raise SystemExit(f"guard tier manifest missing: {MANIFEST}")
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid guard tier manifest JSON: {exc}") from exc


def validate_manifest(payload: dict) -> list[str]:
    errors: list[str] = []
    guards = payload.get("guards")
    if not isinstance(guards, list):
        return ["manifest 'guards' must be a list"]

    paths_seen: set[str] = set()
    for guard in guards:
        if not isinstance(guard, dict):
            errors.append("guard entries must be objects")
            continue
        name = guard.get("name")
        tier = guard.get("tier")
        path = guard.get("path")
        enforces = guard.get("enforces", [])
        if not isinstance(name, str) or not name.strip():
            errors.append(f"guard missing name: {guard}")
            continue
        if not isinstance(path, str) or not path.strip():
            errors.append(f"{name}: missing path")
            continue
        if path in paths_seen:
            errors.append(f"{name}: duplicate path '{path}'")
        paths_seen.add(path)
        if not isinstance(tier, str) or tier not in TIER_ORDER:
            errors.append(f"{name}: invalid tier '{tier}'")
            continue
        if not isinstance(enforces, list) or not enforces:
            errors.append(f"{name}: enforces must be non-empty list")
            continue
        for enforced in enforces:
            if enforced not in TIER_ORDER:
                errors.append(f"{name}: invalid enforced tier '{enforced}'")
                continue
            if TIER_ORDER[tier] < TIER_ORDER[enforced]:
                errors.append(
                    f"{name}: guard tier '{tier}' cannot enforce higher tier '{enforced}'"
                )
        file_path = ROOT / path
        if not file_path.exists():
            errors.append(f"{name}: path '{path}' not found")
    return errors


def main() -> int:
    payload = load_manifest()
    errors = validate_manifest(payload)
    if errors:
        for err in errors:
            print(f"[guard-tier] {err}", file=sys.stderr)
        return 1
    print("guard tier manifest OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
