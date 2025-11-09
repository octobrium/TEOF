#!/usr/bin/env python3
"""CI guard for autonomy module consolidation receipts."""
from __future__ import annotations

from tools.autonomy import module_consolidate


def main() -> int:
    return module_consolidate.main(["guard"])


if __name__ == "__main__":
    raise SystemExit(main())
