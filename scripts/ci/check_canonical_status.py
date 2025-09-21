#!/usr/bin/env python3
"""
check_canonical_status.py

Purpose: Advisory check to ensure canonical governance files are uniquely
designated and present. Prints WARN lines on mismatch; exits 0.

Rules:
  - Exactly these files should declare `Role: Canonical`:
      L0: governance/core/L0 - observation/observation.md
      L1: governance/core/L1 - principles/canonical-teof.md
      L2: governance/core/L2 - objectives/objectives.md
      L3: governance/core/L3 - properties/properties.md
      L4: governance/core/L4 - architecture/architecture.md
      L5: governance/core/L5 - workflow/workflow.md
  - If additional files claim `Role: Canonical`, print WARN.
  - If expected files are missing `Role: Canonical`, print WARN.

This script is non-blocking by design (exit code 0) and intended to be used
as a periodic audit or local preflight aid.
"""
from __future__ import annotations
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

EXPECTED = [
    Path("governance/core/L0 - observation/observation.md"),
    Path("governance/core/L1 - principles/canonical-teof.md"),
    Path("governance/core/L2 - objectives/objectives.md"),
    Path("governance/core/L3 - properties/properties.md"),
    Path("governance/core/L4 - architecture/architecture.md"),
    Path("governance/core/L5 - workflow/workflow.md"),
]


def has_role_canonical(p: Path) -> bool:
    try:
        with p.open("r", encoding="utf-8", errors="ignore") as f:
            head = f.read(4096)
        return "Role: Canonical" in head
    except FileNotFoundError:
        return False


def main() -> int:
    core = ROOT / "governance" / "core"
    if not core.is_dir():
        print("WARN: governance/core not found; skipping canonical check")
        return 0

    expected_abs = { (ROOT / p).resolve() for p in EXPECTED }

    found = set()
    for p in core.rglob("*.md"):
        try:
            if has_role_canonical(p):
                found.add(p.resolve())
        except Exception:
            continue

    missing = [p for p in expected_abs if p not in found]
    extras = [p for p in found if p not in expected_abs]

    if not missing and not extras:
        print(f"OK: canonical headers validated ({len(found)})")
        return 0

    if missing:
        for m in sorted(missing):
            rel = m.relative_to(ROOT)
            print(f"WARN: expected canonical missing header: {rel}")
    if extras:
        for e in sorted(extras):
            rel = e.relative_to(ROOT)
            print(f"WARN: unexpected canonical header present: {rel}")

    # non-blocking
    return 0


if __name__ == "__main__":
    sys.exit(main())

