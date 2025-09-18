#!/usr/bin/env python3
"""Lightweight usage telemetry logger (optional module)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
USAGE_DIR = ROOT / "_report" / "usage"
USAGE_LOG = USAGE_DIR / "tools.jsonl"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


def record_usage(tool: str, *, action: str = "run", extra: Mapping[str, Any] | None = None) -> None:
    """Append a usage record for a helper/CLI.

    Use sparingly—delete this module if telemetry is undesired. Records stay local under
    `_report/usage/tools.jsonl` for auditability.
    """

    entry: dict[str, Any] = {
        "tool": tool,
        "action": action,
        "ts": _now_iso(),
    }
    if extra:
        entry.update(dict(extra))

    USAGE_DIR.mkdir(parents=True, exist_ok=True)
    with USAGE_LOG.open("a", encoding="utf-8") as fh:
        json.dump(entry, fh, ensure_ascii=False)
        fh.write("\n")
