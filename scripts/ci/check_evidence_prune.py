#!/usr/bin/env python3
"""CI guard for evidence_usage + prune cadence receipts."""
from __future__ import annotations

from tools.automation import evidence_prune


def main() -> int:
    return evidence_prune.main(["guard"])


if __name__ == "__main__":
    raise SystemExit(main())
