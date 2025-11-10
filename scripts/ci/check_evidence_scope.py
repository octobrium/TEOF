#!/usr/bin/env python3
"""Ensure every schema v1 plan satisfies evidence_scope requirements."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECEIPT_DIR = ROOT / "_report" / "usage" / "evidence-scope"


def main() -> int:
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable or "python3",
        "-m",
        "tools.planner.evidence_scope",
        "--all",
        "--fail-on-missing",
        "--fail-on-missing-receipts",
        "--receipt-dir",
        str(RECEIPT_DIR),
    ]
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
