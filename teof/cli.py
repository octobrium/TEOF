"""Compatibility shim for `python -m teof.cli` entry point."""
from __future__ import annotations

from .bootloader import main as _main


def main() -> int:
    return _main()


if __name__ == "__main__":
    raise SystemExit(main())
