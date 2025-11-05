"""Helpers shared by repo-local CLI command modules."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from teof._paths import repo_root

DEFAULT_ROOT = repo_root(default=Path(__file__).resolve().parents[2])


def module_root(module: Any, default: Path = DEFAULT_ROOT) -> Path:
    """Return the repo root advertised by *module* (falls back to DEFAULT_ROOT)."""

    candidate = getattr(module, "ROOT", None)
    if candidate is None:
        return default
    return Path(candidate)


def relpath(path: Path, base: Path = DEFAULT_ROOT) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


__all__ = ["DEFAULT_ROOT", "module_root", "relpath"]
