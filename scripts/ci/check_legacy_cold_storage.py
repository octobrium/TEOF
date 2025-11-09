#!/usr/bin/env python3
"""CI guard for legacy artifact cold storage freshness."""
from __future__ import annotations

from tools.artifacts import cold_storage


def main() -> int:
    return cold_storage.main(["guard"])


if __name__ == "__main__":
    raise SystemExit(main())
