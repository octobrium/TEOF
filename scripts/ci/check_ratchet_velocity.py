#!/usr/bin/env python3
"""CI guard ensuring systemic ratchet momentum stays positive."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from tools.metrics import ratchet as ratchet_mod

ROOT = Path(__file__).resolve().parents[2]
HISTORY_PATH = ROOT / ratchet_mod.HISTORY_DIR / "ratchet-history.jsonl"

MIN_INDEX = float(os.getenv("TEOF_RATCHET_MIN_INDEX", "0.95"))
MIN_CLOSURE = float(os.getenv("TEOF_RATCHET_MIN_CLOSURE", "0.2"))
MAX_RISK_MULTIPLIER = float(os.getenv("TEOF_RATCHET_MAX_RISK_MULTIPLIER", "1.5"))


def _load_latest(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as stream:
            lines = [line.strip() for line in stream.readlines() if line.strip()]
    except OSError:
        return None
    if not lines:
        return None
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return None


def main() -> int:
    latest = _load_latest(HISTORY_PATH)
    if latest is None:
        print("::warning::ratchet history missing; run `teof scan --out <dir>` to seed metrics", file=sys.stderr)
        return 0

    index = float(latest.get("ratchet_index", 0.0))
    closure_velocity = float(latest.get("closure_velocity", 0.0))
    risk_load = float(latest.get("risk_load", 0.0))
    complexity = float(latest.get("complexity_added", 0.0))

    failures: list[str] = []
    if index < MIN_INDEX:
        failures.append(f"ratchet_index {index:.3f} below threshold {MIN_INDEX:.3f}")
    if closure_velocity < MIN_CLOSURE:
        failures.append(f"closure_velocity {closure_velocity:.3f} below minimum {MIN_CLOSURE:.3f}")
    threshold = max(complexity * MAX_RISK_MULTIPLIER, 1.0)
    if risk_load > threshold:
        failures.append(f"risk_load {risk_load:.3f} exceeds {MAX_RISK_MULTIPLIER:.2f}x complexity ({threshold:.3f})")

    if failures:
        print("::error::systemic ratchet guard tripped:", file=sys.stderr)
        for failure in failures:
            print(f"::error::{failure}", file=sys.stderr)
        return 1

    print(
        f"[ratchet] index={index:.3f} closure={closure_velocity:.3f} risk={risk_load:.3f} complexity={complexity:.3f}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
