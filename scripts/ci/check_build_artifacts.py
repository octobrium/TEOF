#!/usr/bin/env python3
"""CI wrapper for the build artifact guard."""
from __future__ import annotations

from tools.autonomy import build_guard


def main() -> int:
    return build_guard.main([])


if __name__ == "__main__":
    raise SystemExit(main())
