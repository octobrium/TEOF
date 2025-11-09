#!/usr/bin/env python3
"""Validate the agent coordination bus artifacts."""
from __future__ import annotations

from pathlib import Path

from tools.autonomy.bus_guard import BusGuard


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    guard = BusGuard(ROOT)
    issues = guard.run(autofix=False)

    if issues:
        for issue in issues:
            location = issue.path
            if issue.line is not None:
                location = f"{location} line {issue.line}"
            print(f"::error::{location} {issue.message}")
        return 1

    print("::notice::agent bus artifacts validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
