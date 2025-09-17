#!/usr/bin/env python3
"""Run the minimal evaluation battery with runner receipts."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools" / "runner" / "run.py"


def main() -> int:
    cmd = [
        "python3",
        str(RUNNER),
        "--label",
        "planner-eval-minimal",
        "--receipt-dir",
        str(ROOT / "_report" / "planner"),
        "--",
        "python3",
        "-m",
        "pytest",
        "tests/test_planner_validation.py",
        "tests/test_planner_cli.py",
    ]
    proc = subprocess.run(cmd)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
