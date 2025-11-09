#!/usr/bin/env python3
"""CI guard verifying receipts stream pointer freshness and integrity."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from tools.autonomy import receipts_stream_guard as guard


ROOT = Path(__file__).resolve().parents[2]
POINTER_REL = Path("_report") / "usage" / "receipts-index" / "latest.json"


def _env_max_age_hours() -> float | None:
    raw = os.environ.get("RECEIPTS_STREAM_MAX_AGE_HOURS")
    if raw is None:
        return guard.DEFAULT_MAX_AGE_HOURS
    try:
        value = float(raw)
    except ValueError as exc:  # pragma: no cover - best-effort guardrail
        raise guard.GuardError("invalid RECEIPTS_STREAM_MAX_AGE_HOURS; expected float hours") from exc
    return value if value > 0 else None


def _pointer_path() -> Path:
    return ROOT / POINTER_REL


def main() -> int:
    try:
        message = guard.run(pointer=_pointer_path(), max_age_hours=_env_max_age_hours())
    except guard.GuardError as exc:
        print(f"receipts_stream_guard: {exc}", file=sys.stderr)
        return 1
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
