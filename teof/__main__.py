"""Allow `python -m teof …` to invoke the repo-local bootloader."""
from __future__ import annotations

from teof.bootloader import main


if __name__ == "__main__":  # pragma: no cover - thin entrypoint
    raise SystemExit(main())
